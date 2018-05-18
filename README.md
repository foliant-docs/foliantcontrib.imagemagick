# ImageMagick Preprocessor

This tool provides additional processing of images that referred in Markdown source, with [ImageMagick](https://imagemagick.org/).

## Installation

```bash
$ pip install foliantcontrib.imagemagick
```

## Config

To enable the preprocessor, add `imagemagick` to `preprocessors` section in the project config:

```yaml
preprocessors:
    - imagemagick
```

The preprocessor has a number of options with the following default values:

```yaml
preprocessors:
    - imagemagick:
        convert_path: convert
        cache_dir .imagemagickcache
```

`convert_path`
:   Path to `convert` binary, a part of ImageMagick.

`cache_dir`
:   Directory to store processed images. These files can be reused later.

## Usage

Suppose you want to apply the following command to your picture `image.eps`:

```bash
$ convert image.eps -resize 600 -background Orange label:'Picture' +swap -gravity Center -append image.jpg
```

This command takes the source EPS image `image.eps`, resizes it, puts a text label over the picture, and writes the result into new file `image.jpg`. The suffix of output file name specifies that the image must be converted into JPEG format.

To use the ImageMagick preprocessor to do the same, enclose one or more image references in your Markdown source between `<<magick>` and `</magick>` tags.

```markdown
<<magick command_params="-resize 600 -background Orange label:'Picture' +swap -gravity Center -append" output_format="jpg">
![Optional Caption](image.eps)
</magick>
```

Use `output_format` attribute to specify the suffix of output file name. The whole output file name will be generated automatically.

Use `command_params` attribute to specify the string of parameters that should be passed to ImageMagick `convert` binary.

Instead of using `command_params` attribute, you may specify each parameter as its own attribute with the same name:

```markdown
<<magick resize="600" background="Orange label:'Picture' +swap" gravity="Center" append="true" output_format="jpg">
![Optional Caption](image.eps)
</magick>
```
