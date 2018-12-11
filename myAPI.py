from tweepy import API
#from tweepy.binder import bind_api
from mybinder import my_bind_api


class myAPI(API):
    @staticmethod
    def _pack_image(filename, max_size, form_field="image", f=None):
        """Pack image from file into multipart-formdata post body"""

        # Don't do any checking of image file - because it's not a file (muahaha)
        ## image must be less than 700kb in size if f is None:
            #try:
                #if os.path.getsize(filename) > (max_size * 1024):
                    #raise TweepError('File is too big, must be less than %skb.' % max_size)
            #except os.error as e:
                #raise TweepError('Unable to access file: %s' % e.strerror)
#
            ## build the mulitpart-formdata body
            #fp = open(filename, 'rb')
        #else:
            #f.seek(0, 2)  # Seek to end of file
            #if f.tell() > (max_size * 1024):
                #raise TweepError('File is too big, must be less than %skb.' % max_size)
            #f.seek(0)  # Reset to beginning of file
            #fp = f
#
        ## image must be gif, jpeg, or png
        #file_type = mimetypes.guess_type(filename)
        #if file_type is None:
            #raise TweepError('Could not determine file type')
        #file_type = file_type[0]
        #if file_type not in ['image/gif', 'image/jpeg', 'image/png']:
            #raise TweepError('Invalid file type for image: %s' % file_type)
#
        #if isinstance(filename, six.text_type):
            #filename = filename.encode("utf-8")

        #BOUNDARY = b'Tw3ePy'
        #body = list()
        #body.append(b'--' + BOUNDARY)
        #body.append('Content-Disposition: form-data; name="{0}";'
                    #' filename="{1}"'.format(form_field, filename)
                    #.encode('utf-8'))
#
        #file_type = 'image/jpeg'
        #body.append('Content-Type: {0}'.format(file_type).encode('utf-8'))
        #body.append(b'')
#
        #body.append(fp.read())
#
        #body.append(b'--' + BOUNDARY + b'--')
        #body.append(b'')
        #fp.close()
        #body = b'\r\n'.join(body)

        # no longer need to build body because we are sending image as b64-encoded string
        body = "I ain't got no body"

        # build headers
        # set appropriate header type for urlencoded base64 image string
        headers = {
            #'Content-Type': 'multipart/form-data; boundary=Tw3ePy',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(body))
        }

        return headers, body


    def media_upload(self, filename, *args, **kwargs):
        """ :reference: https://dev.twitter.com/rest/reference/post/media/upload
            :allowed_param:
        """
        f = kwargs.pop('file', None)
        headers, post_data = myAPI._pack_image(filename, 3072, form_field='media', f=f)

        # rather than constructing post_data, use straight-up encoded image string as body of request
        #kwargs.update({'headers': headers, 'post_data': post_data})
        kwargs.update({'headers': headers, 'media_data': f})

        return my_bind_api(
            api=self,
            path='/media/upload.json',
            method='POST',
            payload_type='media',
            allowed_param=[],
            require_auth=True,
            upload_api=True
        )(*args, **kwargs)

