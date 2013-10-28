## Demo
<http://upload.reidransom.com/>

## User Experience
A user visits the page and is presented with a file chooser for uploading videos and a list of existing videos.

When a file is chosen, it gets immediately uploaded to Amazon S3.  After that the user can refresh the page to see the video's transfer/transcode status.

## Behind The Scenes
After the initial S3 upload, the page sends an AJAX request which kicks off the transfer/transcode process:

1. The original video is downloaded to the server (where this Flask app is running) with `curl`.
2. Original video metadata is collected with `ffmpeg`.
3. The original video is transcoded to iPhone video format with `ffmpeg`.
4. iPhone video metadata is collected with `ffmpeg`.
5. The iPhone video is uploaded to S3.

## Dependencies
* [FFmpeg](http://ffmpeg.org/)
  * [From source](https://github.com/stvs/ffmpeg-static) - recommended because it includes libfaac
  * [OS X builds](http://www.evermeet.cx/ffmpeg/)
  * [Linux builds](http://ffmpeg.gusari.org/static/)
* [Flask](http://flask.pocoo.org/)
* [SQLAlchemy](http://docs.sqlalchemy.org/en/rel_0_8/)
* [boto](http://docs.pythonboto.org/en/latest/)

## Configuration
Have a look at [the mule uploader setup instructions](https://github.com/cinely/mule-uploader#set-up).

You'll want to edit the `settings.py` file which is very similar to mule-uploader but with the following additions:

* CONFIG_ROOT - Default location of `aws.txt` config file, `ffmpeg` binary, `tmp` folder, and `database.db` sqlite database file.  If this is undefined or doesn't exist the settings will check `~/.reiduploader/` (which is useful for development).
* FFMPEG - Location of your `ffmpeg` binary.  This should be executable by your webserver.
* TMPDIR - Folder for temp storage.  This should be read/writeable by your webserver.
* MIME_TYPES - A hash of allowed file extensions and their mime types.
* FFMPEG_PRESET - `ffmpeg` command line args.

## Development
The development server can be launched with the following command:

    $ ./make serve

Tests can be run with:

    $ ./make test

or you can run individual tests like this:

    $ python -m unittest tests.test_worker.TestWorker.test_download_url

With minimal effort you could deploy to webfaction  by editing `make.py` and running:

    $ ./make stage

## Roadmap
Mixdown 5.1 tracks to mono with `sox`.

Remove dependency on `curl`.

Ajax refresh button so the user can refresh the video list in the middle of an upload.  The browser would send last time checked, server sends list of videos added since.  This could also auto-refresh every 3 minutes or so.

Framerate conversion for videos with framerates too high for iPhone.

Javascript testing.

Account for files with multiple audio *streams*.

Account for audio only files.

Stream directly from S3 to `ffmpeg` then back up to S3 w/o creating temp files.  This would only work well for stream-able codecs.

Properly mixdown 5.1/7.1 to stereo with `sox`.

Realtime progress indicator.  This would involve parsing `ffmpeg` output as well as more database/ajax stuff.

## License
The MIT License (MIT)

Copyright (c) 2013 Reid Ransom

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

## References
* [mule uplaoder](https://github.com/cinely/mule-uploader)
* [wsgi config directives](http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives)
* [webfaction flask install script](http://community.webfaction.com/questions/12718/installing-flask)
* [deploying flask on webfaction](http://flask.pocoo.org/snippets/65/)
* [python on webfaction](http://docs.webfaction.com/software/python.html)
* [h264 settings for ios](http://blog.zencoder.com/2012/01/24/encoding-settings-for-perfect-ipadiphone-video/)
* [Using setfacl and getfacl on webfaction](https://docs.webfaction.com/software/general.html#setting-file-permissions)
* [S3 API Reference](http://docs.pythonboto.org/en/latest/ref/s3.html)
