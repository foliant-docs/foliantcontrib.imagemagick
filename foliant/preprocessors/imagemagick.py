'''
Preprocessor for Foliant documentation authoring tool.

Provides additional processing of images
that referred in Markdown sources with ImageMagick.
'''

import re
from pathlib import Path
from hashlib import md5
from subprocess import run, PIPE, STDOUT, CalledProcessError
from typing import Dict
OptionValue = int or float or bool or str

from foliant.preprocessors.base import BasePreprocessor


class Preprocessor(BasePreprocessor):
    defaults = {
        'convert_path': 'convert',
        'cache_dir': Path('.imagemagickcache'),
    }

    tags = 'magick',

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._cache_dir_path = self.project_path / self.options['cache_dir']
        self._current_dir_path = self.working_dir

        self.logger = self.logger.getChild('imagemagick')

        self.logger.debug(f'Preprocessor inited: {self.__dict__}')

    def _get_processed_img_ref(
        self,
        img_path: str,
        img_caption: str,
        options: Dict[str, OptionValue]
    ) -> str:

        source_img_path = self._current_dir_path / img_path
        processed_img_format = 'png'
        command_params = []
        command_params_string = ''

        for option_name, option_value in options.items():
            if isinstance(option_value, bool):
                if option_value:
                    command_params.append(f'-{option_name}')

            else:
                option_value = str(option_value)
                option_value = option_value.replace('&quot;', '"')
                option_value = option_value.replace('&#34;', '"')

                if option_name == 'output_format':
                    processed_img_format = option_value

                elif option_name == 'command_params':
                    command_params_string += f'{option_value}'

                else:
                    if option_name == option_value:
                        command_params.append(f'-{option_name}')

                    else:
                        command_params.append(f'-{option_name} {option_value}')

        if command_params_string and command_params:
            command_params_string += ' '

        command_params_string += ' '.join(command_params)

        self.logger.debug(
            f'Source image path: {source_img_path}, ' \
            f'image caption: {img_caption}, ' \
            f'processed image format: {processed_img_format}, ' \
            f'command params: {command_params_string}'
        )

        img_hash = md5(f'{command_params_string}'.encode())

        with open(source_img_path.absolute().as_posix(), 'rb') as source_img_file:
            source_img_file_body = source_img_file.read()
            img_hash.update(f'{source_img_file_body}'.encode())

        processed_img_path = self._cache_dir_path / f'{img_hash.hexdigest()}.{processed_img_format}'
        processed_img_ref = f'![{img_caption}]({processed_img_path.absolute().as_posix()})'

        self.logger.debug(f'Processed image path: {processed_img_path}')

        if processed_img_path.exists():
            self.logger.debug(f'Processed image found in cache')

            return processed_img_ref

        processed_img_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            command = f'{self.options["convert_path"]} ' \
                      f'{source_img_path.absolute().as_posix()} ' \
                      f'{command_params_string} ' \
                      f'{processed_img_path.absolute().as_posix()}'

            run(command, shell=True, check=True, stdout=PIPE, stderr=STDOUT)

            self.logger.debug(f'Processed image saved')

        except CalledProcessError as exception:
            self.logger.error(str(exception))

            raise RuntimeError(
                f'Processing of image {img_path} failed: {exception.output.decode()}'
            )

        return processed_img_ref

    def _process_imagemagick(self, options: Dict[str, OptionValue], body: str) -> str:
        src_img_ref_pattern = re.compile('\!\[(?P<caption>[^\[\]]*)\]\((?P<path>((?!:\/\/)[^\(\)\s])+)\)')

        def _sub(src_img_ref) -> str:
            return self._get_processed_img_ref(
                src_img_ref.group('path'),
                src_img_ref.group('caption'),
                options
            )

        return src_img_ref_pattern.sub(_sub, body)

    def process_imagemagick(self, content: str) -> str:
        def _sub(magick_block) -> str:
            return self._process_imagemagick(
                self.get_options(magick_block.group('options')),
                magick_block.group('body')
            )

        return self.pattern.sub(_sub, content)

    def apply(self):
        self.logger.info('Applying preprocessor')

        for markdown_file_path in self.working_dir.rglob('*.md'):
            with open(markdown_file_path, encoding='utf8') as markdown_file:
                content = markdown_file.read()

            processed_content = self.process_imagemagick(content)

            if processed_content:
                with open(markdown_file_path, 'w', encoding='utf8') as markdown_file:
                    self._current_dir_path = markdown_file_path.parent
                    markdown_file.write(processed_content)

        self.logger.info('Preprocessor applied')
