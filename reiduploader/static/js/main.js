/* globals $, _config, mule_upload */

function reid_upload (config) {

    var log_el = $('#log')

    function format_size (num_bytes) {
        if (num_bytes <= 1024 * 0.8) {
            return num_bytes + " B"
        }
        else if (num_bytes <= 1024 * 1024 * 0.8) {
            return parseInt(num_bytes / 1024, 10) + "." + parseInt(num_bytes / 1024 * 10, 10) % 10 + " KB"
        }
        else if(num_bytes <= 1024 * 1024 * 1024 * 0.8) {
            return parseInt(num_bytes / 1024 / 1024, 10) + "." + parseInt(num_bytes / 1024 / 1024 * 10, 10) % 10 + " MB"
        }
        else {
            return parseInt(num_bytes / 1024 / 1024 / 1024, 10) + "." + parseInt(num_bytes / 1024 / 1024 / 1024 * 10, 10) % 10 + " GB"
        }
    }

    // Log upload messages
    function uplog (msg) {
        log_el.prepend(msg)
    }

    // Return the filename's extension
    // todo: check that this is an alpha-numeric string and make all lowercase
    function get_file_ext (filename) {
        var parts = filename.split('.')
        return '.' + parts[parts.length - 1]
    }

    var last_update = null;
    var last_uploaded = null;
    var settings = {
        file_input: document.getElementById("file"),
        max_size: 50 * (1 << 30), // 50 gb
        on_error: function() {
            uplog("Error occurred! You can help me fix this by filing a bug report here: https://github.com/cinely/mule-uploader/issues\n");
        },
        on_select: function(fileObj) {
            uplog("File selected\n");

            // todo: append the entire filename.  strip out non-whitelisted characters.
            this.settings.key += get_file_ext(fileObj.name)

            var size = fileObj.size;
            var num_chunks = Math.ceil(size / (6 * 1024 * 1024));
            var chunk_width = $(".upload-progress").width() / num_chunks;
            for (var i=0; i < num_chunks; i += 1) {
                var chunk = $("<div class='chunk'>");
                chunk.css({
                    'width': chunk_width + 'px',
                    'height': "0%",
                });
                $(".upload-progress").append(chunk);
            }
            $('.upload-progress').css('width', null);
        },
        on_start: function(fileObj) {
            uplog("Upload started\n");
        },
        on_progress: function(bytes_uploaded, bytes_total) {
            if(!last_update || (new Date() - last_update) > 1000) {
                var percent = bytes_uploaded / bytes_total * 100;
                var speed = (bytes_uploaded - last_uploaded) / (new Date() - last_update) * 1000;
                last_update = new Date();
                last_uploaded = bytes_uploaded;
                $('.progress .bar').width(percent / 100 * $('.progress').width());
                var log = "Upload progress: " + format_size(bytes_uploaded) + " / " +
                    format_size(bytes_total) + " (" + parseInt(percent, 10) + "." +
                    parseInt(percent * 10, 10) % 10 + "%)";
                if (speed) {
                    log += "; speed: " + format_size(speed) + "/s";
                }
                uplog(log + "\n");
            }
        },
        on_chunk_progress: function(chunk, progress, total) {
            var height = $('.upload-progress').height();
            $($('.upload-progress .chunk').get(chunk)).css({
                'height': Math.ceil((progress / total) * height) + "px",
                'margin-top': Math.floor(((total - progress) / total) * height) + "px"
            });
        },
        on_init: function() {
            uplog("Uploader initialized\n");
        },
        on_complete: function() {
            var url = "http://" + config.bucket + ".s3.amazonaws.com/" + this.settings.key;
            uplog("Upload complete!\n");
            uplog("The file url is " + url + ".\n");
        },
        on_chunk_uploaded: function() {
            uplog("Chunk finished uploading\n");
        }
    };
    $.extend(settings, config)
    mule_upload(settings)

}
