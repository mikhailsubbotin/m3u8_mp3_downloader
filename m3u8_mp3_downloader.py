# Simple HLS MP3 Downloader by Mikhail Subbotin
# https://github.com/mikhailsubbotin

from Crypto.Cipher import AES
import argparse, arrow, m3u8, os, requests, sys

def download_object(url):
    try:
        result = requests.get(url)
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print ("HTTP ERROR:", err)
        return None
    except requests.exceptions.ConnectionError:
        print ("CONNECTION ERROR!")
        return None
    except requests.exceptions.Timeout as err:
        print ("TIMEOUT ERROR:", err)
        return None
    except requests.exceptions.RequestException as err:
        print ("ERROR:", err)
        return None
    return result

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-d', '--destination-file', dest = 'destination_filename', help = 'destination file path')
    ap.add_argument('m3u8_hls_url', help = 'source hls url')
    args = ap.parse_args()
    temporary_ts_filename = arrow.now().format('YYYYMMDDHHmmss')
    if args.destination_filename:
        destination_filename = args.destination_filename
    else: destination_filename = temporary_ts_filename + '.mp3'
    temporary_ts_filename += '.ts'
    r = download_object(args.m3u8_hls_url)
    if not r: sys.exit()
    print(args.m3u8_hls_url)
    try: m3u8_object = m3u8.loads(r.text, uri = args.m3u8_hls_url)
    except:
        print('ERROR: Invalid M3U8 data!')
        sys.exit()
    if m3u8_object.playlist_type == 'event' or m3u8_object.playlist_type == 'vod':
        try: f = open(temporary_ts_filename, 'wb')
        except IOError as e:
            print('ERROR: Unable to create file! Code:', e.errno)
            sys.exit()
        for s in m3u8_object.segments:
            print(s.absolute_uri, end = ' ')
            if m3u8_object.keys != [None] and s.key.method == 'AES-128':
                r = download_object(s.key.uri)
                if not r:
                    f.close()
                    os.remove(temporary_ts_filename)
                    sys.exit()
                if s.key.iv:
                    iv = s.key.iv
                else: iv = 16 * b'\x00'
                aes = AES.new(r.content, AES.MODE_CBC, iv)
                r = download_object(s.absolute_uri)
                if not r:
                    f.close()
                    os.remove(temporary_ts_filename)
                    sys.exit()
                print(r.headers['content-length'] + ' byte(s)')
                f.write(aes.decrypt(r.content))
            else:
                r = download_object(s.absolute_uri)
                if not r:
                    f.close()
                    os.remove(temporary_ts_filename)
                    sys.exit()
                print(r.headers['content-length'] + ' byte(s)')
                f.write(r.content)
        f.close()
        os.system('ffmpeg -i "' + temporary_ts_filename + '" -c copy "' + destination_filename + '"')
        os.remove(temporary_ts_filename)
    else:
        print('ERROR: Unsupported M3U8 playlist type!')
