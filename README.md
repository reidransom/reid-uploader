## demo urls
* Development - <http://localhost:5000/>
* Staging - <http://upload.reidransom.com/>

## workflow
* mule_upload to s3
* http stream from s3 to avconv
* grab metadata from avconv
* stream from avconv to s3 with boto
* run qtfaststart.py on remote s3 file

### streaming all the way

	browser > s3 > ffmpeg (h264, aac) > s3

Adv: fast, data never hits the hard disk

Dis: can't work sox into this for mixing down 5.1 (maybe mplayer could do the a/v transcode as well as audio mixdown)

### create a temp localfile

	browser > s3 > ffmpeg (h264, audio copy) > localfile
	localfile > sox (mixdown 5.1 to stereo, aac)
	          > ffmpeg (marry h264 and aac) > s3
	delete localfile

Adv: manipulate the file as much as you want

Dis: slower, potentially involves storing lots of data on the hard disk

## todo
* Use [boto.s3.key.Key.set_contents_from_file](https://github.com/boto/boto/blob/develop/boto/s3/key.py#L1063) to stream from avconv to s3:
* Adapt qtfaststart.py to work with s3
* move database.db out of the web root
* stop mule_uploader from giving everything mimetype = application/octet-stream (see mule_uploader.js and settings.py/reiduploader.py)

## references
* [mule uplaoder](https://github.com/cinely/mule-uploader)
* [wsgi config directives](http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives)
* [webfaction flask install script](http://community.webfaction.com/questions/12718/installing-flask)
* [deploying flask on webfaction](http://flask.pocoo.org/snippets/65/)
* [python on webfaction](http://docs.webfaction.com/software/python.html)
* [h264 settings for ios](http://blog.zencoder.com/2012/01/24/encoding-settings-for-perfect-ipadiphone-video/)
* [Using setfacl and getfacl on webfaction](https://docs.webfaction.com/software/general.html#setting-file-permissions)

## good iOS preset

	{
		"name": "High Profile 960x540 h.264",
		"cmd": ["ffmbc", "-i", "{{infile}}", "-vcodec", "libx264", "-acodec", "libfaac", "-ab", "1  28k", "-ac", "2", "-ar", "48k", "-aspect", "16:9", "-vf", "yadif,scale=960:540", "-faststart", "auto", "-x264opts", "cabac=1:ref=3:deblock=1,0,0:analyse=0x3,0x113:me=hex:subme=7:psy=1:psy_rd=1.00,  0.00:me_range=16:chroma_me=1:trellis=1:8x8dct=1:fast_pskip=1:chroma_qp_offset=-2:threads=36:sliced  _threads=0:nr=0:interlaced=0:bluray_compat=0:constrained_intra=0:bframes=3:b_pyramid=2:b_adapt=1:b  _bias=0:weightb=1:open_gop=0:weightp=2:keyint=240:keyint_min=24:scenecut=40:intra_refresh=0:rc_loo  kahead=40:mbtree=1:crf=22:qcomp=0.60:qpmin=0:qpmax=69:qpstep=4:vbv_maxrate=17500:vbv_bufsize=17500  :crf_max=0.0:nal_hrd=none", "{{outfile}}-high-960x540-h264.mp4"]
	}