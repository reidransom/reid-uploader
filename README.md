## demo urls
* Development - <http://localhost:5000/>
* Staging - <http://upload.reidransom.com/>

## workflow
* mule_upload to s3
* http stream from s3 to avconv
* grab metadata from avconv
* stream from avconv to s3 with boto
* run qtfaststart.py on remote s3 file

## todo
* Use [boto.s3.key.Key.set_contents_from_file](https://github.com/boto/boto/blob/develop/boto/s3/key.py#L1063) to stream from avconv to s3:
* Adapt qtfaststart.py to work with s3

## references
* [mule uplaoder](https://github.com/cinely/mule-uploader)
* [wsgi config directives](http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives)
* [webfaction flask install script](http://community.webfaction.com/questions/12718/installing-flask)
* [deploying flask on webfaction](http://flask.pocoo.org/snippets/65/)
* [python on webfaction](http://docs.webfaction.com/software/python.html)