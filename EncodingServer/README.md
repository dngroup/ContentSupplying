# MS-Stream Encoding Server

This code is a nodeJS project that provide a simple upload webpage for a user to upload a video and specify some encoding parameters. Once uploaded, the video is encoded using ffmpeg and MP4Box.

This code has been developped and tested on/for Ubuntu 14.04, Ubuntu 16.04 and Ubuntu 17.04. As the code is using child_process,
the code should not work on Windows and MacOS (but it has not been tested).

## Dependencies

* Install [NodeJS and npm](https://nodejs.org/en/download/current/)
* Install [FFMpeg](https://www.ffmpeg.org/)
* Install [gpac](https://gpac.wp.imt.fr/2011/04/20/compiling-gpac-on-ubuntu/)

## Installation

Install the dependencies:
```
npm install
```

## Using the server

Run the server:
```
npm start
```
or
```
node src/index.js -p <port number | default: 8080>
```

Go to the url [http://localhost:8080/].

Select the parameters and upload a video.

The state of the the encoding can be found at [http://localhost:8080/api/encode/state/{videoId}].

The encoded files are in **./contents/{videoId}/{videoId}**

## Encoding Service

The **Encoding Service** is called in the code using a **videoId** and a list of Encoding Parameters :

```
/**
*   EncodingParameter
*
*   {number} bitrate
*   {number} width
*   {number} height
*   {number} fps
*   {number} segmentDuration
*   {number} gopSize
*
*/
```

The informations of the state of the encoding process are saved in a file at **./contents/state.json**.
```
/**
 *   EncodingState
 *
 *   {string} videoId
 *   {boolean} isReady // When the full encoding process is over
 *   {boolean} isAudioReady // When the audio is encoded
 *   {boolean} isEncoded // When the video are encoded in every quality /!\ that does not mean the full encoding process is over
 *   {[]EncodingParameters} availableQualities // All the EncodingParameters that are already encoded in the process
 *   {number} percentOfCompletion // Percent Of completion according to the number of tasks /!\ this parameter can not be used to provide a good estimation of the time needed to finish the encoding process
 *   {[]Obj} failures // All the tasks that have thrown an error
 */

```

## Dev environment

This code has been developped and tested on Ubuntu 14.04, 16.04, 17.04 with the following versions of the dependencies:

```
node -v

v6.11.0

```

```
npm -v

5.3.0
```

```
ffmpeg -version

ffmpeg version 3.2.4-1build2 Copyright (c) 2000-2017 the FFmpeg developers
built with gcc 6.3.0 (Ubuntu 6.3.0-8ubuntu1) 20170221
configuration: --prefix=/usr --extra-version=1build2 --toolchain=hardened --libdir=/usr/lib/x86_64-linux-gnu --incdir=/usr/include/x86_64-linux-gnu --enable-gpl --disable-stripping --enable-avresample --enable-avisynth --enable-gnutls --enable-ladspa --enable-libass --enable-libbluray --enable-libbs2b --enable-libcaca --enable-libcdio --enable-libebur128 --enable-libflite --enable-libfontconfig --enable-libfreetype --enable-libfribidi --enable-libgme --enable-libgsm --enable-libmp3lame --enable-libopenjpeg --enable-libopenmpt --enable-libopus --enable-libpulse --enable-librubberband --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libspeex --enable-libssh --enable-libtheora --enable-libtwolame --enable-libvorbis --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx265 --enable-libxvid --enable-libzmq --enable-libzvbi --enable-omx --enable-openal --enable-opengl --enable-sdl2 --enable-libdc1394 --enable-libiec61883 --enable-chromaprint --enable-frei0r --enable-libopencv --enable-libx264 --enable-shared
libavutil      55. 34.101 / 55. 34.101
libavcodec     57. 64.101 / 57. 64.101
libavformat    57. 56.101 / 57. 56.101
libavdevice    57.  1.100 / 57.  1.100
libavfilter     6. 65.100 /  6. 65.100
libavresample   3.  1.  0 /  3.  1.  0
libswscale      4.  2.100 /  4.  2.100
libswresample   2.  3.100 /  2.  3.100
libpostproc    54.  1.100 / 54.  1.100
```

```
MP4Box -version

MP4Box - GPAC version 0.5.2-DEV-revVersion: 0.5.2-426-gc5ad4e4+dfsg5-3
GPAC Copyright (c) Telecom ParisTech 2000-2012
GPAC Configuration: --build=x86_64-linux-gnu --prefix=/usr --includedir=${prefix}/include --mandir=${prefix}/share/man --infodir=${prefix}/share/info --sysconfdir=/etc --localstatedir=/var --disable-silent-rules --libdir=${prefix}/lib/x86_64-linux-gnu --libexecdir=${prefix}/lib/x86_64-linux-gnu --disable-maintainer-mode --disable-dependency-tracking --prefix=/usr --libdir=lib/x86_64-linux-gnu --mandir=${prefix}/share/man --extra-cflags=-Wall -fPIC -DPIC -I/usr/include/mozjs -DXP_UNIX -Wdate-time -D_FORTIFY_SOURCE=2 -g -O2 -fstack-protector-strong -Wformat -Werror=format-security --extra-ldflags=-Wl,-Bsymbolic-functions -Wl,-z,relro --enable-joystick --enable-debug --disable-ssl --verbose
Features: GPAC_64_BITS GPAC_HAS_JPEG GPAC_HAS_PNG
```

## Docker

The docker image is **msstream/encodingservice**. The encoding service can be launched using :

```
docker run --rm -d -p 8080:8080 --name=encodingservice  -v /path/to/destination/folder/:/encoding/contents/ msstream/encodingservice
```