import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QSlider
from PyQt5.QtCore import Qt, QSize, QTimer, QRectF, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from src.style.mini_player import (
    mini_player_container_style,
    mini_player_title_style,
    mini_player_separator_style,
    mini_player_button_style,
    mini_player_slider_style,
)


class YouTubeMusicMiniPlayer(QWidget):
    def __init__(self, yt_music_widget, parent=None):
        super().__init__(parent)
        self.yt_music_widget = yt_music_widget
        self._nam = QNetworkAccessManager(self)
        self._art_url = ""
        self._build_ui()
        self._wire_controls()
        self._start_status_timer()

    def _build_ui(self):
        container = QFrame(self)
        container.setStyleSheet(mini_player_container_style())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        self.art_label = QLabel(container)
        self.art_label.setFixedSize(QSize(48, 48))
        self.art_label.setScaledContents(True)
        self.art_label.setStyleSheet("border-radius:6px;background:#111;")
        title_row.addWidget(self.art_label)

        self.lbl_now_playing = QLabel("—", container)
        self.lbl_now_playing.setStyleSheet(mini_player_title_style())
        self.lbl_now_playing.setWordWrap(False)
        self.lbl_now_playing.setMinimumWidth(100)
        self.lbl_now_playing.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_row.addWidget(self.lbl_now_playing, 1)
        layout.addLayout(title_row)

        sep = QFrame(container)
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(mini_player_separator_style())
        layout.addWidget(sep)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(10)

        self.btn_prev = QPushButton("", container)
        self.btn_playpause = QPushButton("", container)
        self.btn_next = QPushButton("", container)
        for btn in (self.btn_prev, self.btn_playpause, self.btn_next):
            btn.setFixedSize(QSize(36, 36))
            btn.setStyleSheet(mini_player_button_style())
            btn.setIconSize(QSize(20, 20))

        controls.addStretch(1)
        controls.addWidget(self.btn_prev)
        controls.addWidget(self.btn_playpause)
        controls.addWidget(self.btn_next)
        controls.addStretch(1)
        layout.addLayout(controls)
        layout.addSpacing(4)

        self._load_icons()
        self.btn_prev.setIcon(self.icon_prev)
        self.btn_next.setIcon(self.icon_next)
        self.btn_playpause.setIcon(self.icon_play)

        self.slider = QSlider(Qt.Horizontal, container)
        self.slider.setRange(0, 1000)
        self.slider.setValue(0)
        self.slider.setStyleSheet(mini_player_slider_style())
        layout.addWidget(self.slider)
        self._seeking = False
        self.slider.sliderPressed.connect(lambda: setattr(self, '_seeking', True))
        self.slider.sliderReleased.connect(self._on_seek_released)
        self.slider.sliderMoved.connect(self._on_slider_moved)

    def _wire_controls(self):
        self.btn_prev.clicked.connect(self.youtube_music_prev)
        self.btn_playpause.clicked.connect(self.youtube_music_toggle)
        self.btn_next.clicked.connect(self.youtube_music_next)

    def _start_status_timer(self):
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(700)
        self.status_timer.timeout.connect(self.update_youtube_music_status)
        self.status_timer.start()

    def _ytmusic_run_js(self, script: str, callback=None):
        try:
            page = self.yt_music_widget.web_view.page()
            if callback:
                page.runJavaScript(script, callback)
            else:
                page.runJavaScript(script)
        except Exception as e:
            print(f"YouTube Music JS error: {e}")

    def youtube_music_prev(self):
        js = r"""
        (function(){
          function api(){ var app=document.querySelector('ytmusic-app'); return app && (app.playerApi || app.playerApi_); }
          var p=api();
          if(p && p.previousTrack){ p.previousTrack(); return 'api'; }
          var btn = document.querySelector('ytmusic-player-bar #previous-button') || document.querySelector('#left-controls #previous-button');
          if(btn){ btn.click(); return 'btn'; }
          var e=new KeyboardEvent('keydown',{key:'P',shiftKey:true,bubbles:true,cancelable:true});
          document.body.dispatchEvent(e);
          return 'kbd';
        })()
        """
        self._ytmusic_run_js(js)

    def youtube_music_next(self):
        js = r"""
        (function(){
          function api(){ var app=document.querySelector('ytmusic-app'); return app && (app.playerApi || app.playerApi_); }
          var p=api();
          if(p && p.nextTrack){ p.nextTrack(); return 'api'; }
          var btn = document.querySelector('ytmusic-player-bar #next-button') || document.querySelector('#left-controls #next-button');
          if(btn){ btn.click(); return 'btn'; }
          var e=new KeyboardEvent('keydown',{key:'N',shiftKey:true,bubbles:true,cancelable:true});
          document.body.dispatchEvent(e);
          return 'kbd';
        })()
        """
        self._ytmusic_run_js(js)

    def youtube_music_toggle(self):
        js = r"""
        (function(){
          function api(){ var app=document.querySelector('ytmusic-app'); return app && (app.playerApi || app.playerApi_); }
          var p=api();
          if(p && p.playPause){ p.playPause(); return 'api'; }
          var btn = document.querySelector('ytmusic-player-bar #play-pause-button') || document.querySelector('#left-controls #play-pause-button');
          if(btn){ btn.click(); return 'btn'; }
          var e=new KeyboardEvent('keydown',{key:' ',bubbles:true,cancelable:true});
          document.body.dispatchEvent(e);
          return 'kbd';
        })()
        """
        self._ytmusic_run_js(js)

    def update_youtube_music_status(self):
        js = r"""
        (function(){
          function api(){ var app=document.querySelector('ytmusic-app'); return app && (app.playerApi||app.playerApi_); }
          function getTitle(){
            var bar=document.querySelector('ytmusic-player-bar');
            var tEl = (bar && (bar.querySelector('.title') || bar.querySelector('#song-title'))) || document.querySelector('ytmusic-player-page #header .title');
            var t = tEl ? tEl.textContent.trim() : (document.title || '').replace(/ - You\u200b?Tube Music$/, '');
            return t;
          }
          function getArt(){
            var img = document.querySelector('ytmusic-player-bar img');
            var src = img && (img.currentSrc || img.src);
            if(!src){
              var el = document.querySelector('ytmusic-player-bar .image, ytmusic-player-bar #thumbnail img, ytmusic-player-page img');
              if(el){ var cs = getComputedStyle(el); var bg = (cs && cs.backgroundImage) || ''; var m = bg.match(/url\("?([^")]+)"?\)/); if(m) src = m[1]; }
            }
            if(src){ src = src.replace(/=w\d+-h\d+/, '=w256-h256'); }
            return src || '';
          }
          function getState(){
            var btn = document.querySelector('ytmusic-player-bar #play-pause-button') || document.querySelector('#left-controls #play-pause-button') || document.querySelector('tp-yt-paper-icon-button#play-pause-button');
            if(!btn) return 'paused';
            var t = btn.getAttribute('title') || btn.getAttribute('aria-label') || '';
            return (/pause/i.test(t)) ? 'playing' : 'paused';
          }
          function getProgress(){
            var p=api(); var cur=0,dur=0;
            if(p){
              try{ if(p.getCurrentTime) cur=p.getCurrentTime(); }catch(e){}
              try{ if(p.getDuration) dur=p.getDuration(); }catch(e){}
              if((!cur||!dur) && p.getProgressState){ try{ var s=p.getProgressState(); if(s){cur=s.current||s.currentTime||0; dur=s.duration||s.total||0;} }catch(e){} }
            }
            if(!dur){ var a=document.querySelector('audio'); if(a){ cur=a.currentTime||0; dur=a.duration||0; } }
            return {cur:cur, dur:dur};
          }
          var pr=getProgress();
          return {title:getTitle(), art:getArt(), state:getState(), cur:pr.cur, dur:pr.dur};
        })()
        """

        def _apply(status):
            try:
                title = ''
                state = 'paused'
                if isinstance(status, dict):
                    title = (status.get('title') or '').strip()
                    state = status.get('state') or 'paused'
                else:
                    title = (status or '').strip()

                if title.endswith(' - YouTube Music'):
                    title = title[:-18]
                if not title:
                    title = '—'
                self.lbl_now_playing.setText(title)

                self.btn_playpause.setIcon(self.icon_pause if state == 'playing' else self.icon_play)

                cur = float(status.get('cur') or 0)
                dur = float(status.get('dur') or 0)
                if not self._seeking and dur > 0:
                    val = int(max(0, min(1000, (cur / dur) * 1000)))
                    self.slider.setValue(val)

                art = (status.get('art') or '').strip() if isinstance(status, dict) else ''
                if art and art != self._art_url:
                    self._set_art_url(art)
            except Exception:
                pass

        self._ytmusic_run_js(js, _apply)

    def _on_slider_moved(self, val: int):
        pass

    def _on_seek_released(self):
        try:
            val = self.slider.value()
            def _seek_with_duration(d):
                try:
                    dur = float((d or {}).get('dur') or 0)
                    if dur > 0:
                        sec = max(0.0, min(dur, (val / 1000.0) * dur))
                        js = """
                        (function(sec){
                          function api(){ var app=document.querySelector('ytmusic-app'); return app && (app.playerApi||app.playerApi_); }
                          var p=api();
                          if(p && p.seekTo){ p.seekTo(sec,true); return 'api.seekTo'; }
                          if(p && p.seek){ p.seek(sec); return 'api.seek'; }
                          var a=document.querySelector('audio'); if(a){ a.currentTime=sec; return 'audio'; }
                          return 'none';
                        })()
                        """.replace(')()', '(' + str(sec) + ')')
                        self._ytmusic_run_js(js)
                finally:
                    self._seeking = False

            status_js = (
                "(function(){ var a=document.querySelector('audio'); var d=a&&a.duration||0;"
                " var p=document.querySelector('ytmusic-app'); p=p&&(p.playerApi||p.playerApi_);"
                " try{ if(p&&p.getDuration) d=p.getDuration(); }catch(e){} return {dur:d||0}; })()"
            )
            self._ytmusic_run_js(status_js, _seek_with_duration)
        except Exception:
            self._seeking = False

    def _svg_icon(self, path: str, size: int = 20) -> QIcon:
        mask = QPixmap(size, size)
        mask.fill(Qt.transparent)
        renderer = QSvgRenderer(path)
        p = QPainter(mask)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            renderer.render(p, QRectF(0, 0, size, size))
        finally:
            p.end()

        colored = QPixmap(size, size)
        colored.fill(Qt.transparent)
        p = QPainter(colored)
        try:
            p.fillRect(0, 0, size, size, QColor(255, 255, 255))
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.drawPixmap(0, 0, mask)
        finally:
            p.end()
        return QIcon(colored)

    def _load_icons(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        media_dir = os.path.join(base_dir, 'Media')
        self.icon_prev = self._svg_icon(os.path.join(media_dir, 'previous.svg'))
        self.icon_next = self._svg_icon(os.path.join(media_dir, 'next.svg'))
        self.icon_play = self._svg_icon(os.path.join(media_dir, 'playing.svg'))
        self.icon_pause = self._svg_icon(os.path.join(media_dir, 'pause.svg'))

    def _set_art_url(self, url: str):
        self._art_url = url
        try:
            req = QNetworkRequest(QUrl(url))
            reply = self._nam.get(req)
            reply.finished.connect(lambda r=reply: self._on_art_reply(r))
        except Exception:
            pass

    def _on_art_reply(self, reply):
        try:
            if reply.error() == reply.NoError:
                data = reply.readAll()
                pix = QPixmap()
                if pix.loadFromData(bytes(data)):
                    sz = self.art_label.size()
                    self.art_label.setPixmap(pix.scaled(sz, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        finally:
            reply.deleteLater()
