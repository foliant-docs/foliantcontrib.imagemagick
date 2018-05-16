'''
TODO
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
        magick_params: str,
        processed_img_format: str or None
    ) -> str:

        source_img_path = self._current_dir_path / img_path

        img_hash = md5(f'{magick_params}'.encode())

        with open(source_img_path.absolute().as_posix(), 'rb') as source_img_file:
            source_img_file_body = source_img_file.read()
            img_hash.update(f'{source_img_file_body}'.encode())

        if not processed_img_format:
            processed_img_format = 'png'

        self.logger.debug(
            f'Source image path: {source_img_path}, ' \
            f'image caption: {img_caption}, ' \
            f'ImageMagick params: {magick_params}, ' \
            f'processed image format: {processed_img_format}'
        )

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
                      f'{magick_params} ' \
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
                options.get('params'),
                options.get('format')
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

            with open(markdown_file_path, 'w', encoding='utf8') as markdown_file:
                self._current_dir_path = markdown_file_path.parent
                markdown_file.write(self.process_imagemagick(content))

        self.logger.info('Preprocessor applied')
