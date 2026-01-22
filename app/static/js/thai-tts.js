/**
 * Thai Text-to-Speech Module
 * 使用浏览器 Web Speech API 实现泰语发音
 */

const ThaiTTS = {
    // 配置
    config: {
        lang: 'th-TH',
        rate: 0.8,  // 语速稍慢，便于学习
        pitch: 1,
        volume: 1
    },

    // 检查浏览器是否支持
    isSupported: function() {
        return 'speechSynthesis' in window;
    },

    // 播放泰语发音
    speak: function(text, callback) {
        if (!this.isSupported()) {
            console.warn('浏览器不支持语音合成');
            return false;
        }

        // 取消正在播放的语音
        speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = this.config.lang;
        utterance.rate = this.config.rate;
        utterance.pitch = this.config.pitch;
        utterance.volume = this.config.volume;

        // 尝试选择泰语语音
        const voices = speechSynthesis.getVoices();
        const thaiVoice = voices.find(v => v.lang.startsWith('th'));
        if (thaiVoice) {
            utterance.voice = thaiVoice;
        }

        if (callback) {
            utterance.onend = callback;
        }

        speechSynthesis.speak(utterance);
        return true;
    },

    // 停止播放
    stop: function() {
        if (this.isSupported()) {
            speechSynthesis.cancel();
        }
    },

    // 创建发音按钮
    createSpeakButton: function(text, size) {
        size = size || 'normal';  // 'small', 'normal', 'large'

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'speak-btn speak-btn-' + size;
        btn.title = '点击播放发音';
        btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>';

        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            ThaiTTS.speak(text);

            // 添加播放动画
            btn.classList.add('speaking');
            setTimeout(function() {
                btn.classList.remove('speaking');
            }, 1000);
        });

        return btn;
    },

    // 初始化：加载语音列表
    init: function() {
        if (!this.isSupported()) {
            return;
        }

        // 某些浏览器需要等待语音列表加载
        if (speechSynthesis.getVoices().length === 0) {
            speechSynthesis.addEventListener('voiceschanged', function() {
                // 语音列表已加载
            });
        }
    }
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    ThaiTTS.init();
});
