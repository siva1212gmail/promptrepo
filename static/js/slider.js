/**
 * PROMPT PETTI — Draggable Before / After Comparison Slider
 * Touch + Mouse Pointer Events, Keyboard Navigation, Pan-Y Scroll Friendly
 */

(function () {
    'use strict';

    window.BeforeAfterSlider = {
        active: false,
        container: null,
        handle: null,
        afterImageWrap: null,
        currentPercent: 50,

        init: function (containerSelector) {
            const container = typeof containerSelector === 'string'
                ? document.querySelector(containerSelector)
                : containerSelector;

            if (!container) return;
            this.container = container;
            this.handle = container.querySelector('#slider-handle');
            this.afterImageWrap = container.querySelector('.slider-image-after');

            if (!this.handle || !this.afterImageWrap) return;

            // Reset to 50%
            this.setPosition(50);

            // Bind pointer events
            this.onPointerDown = this.onPointerDown.bind(this);
            this.onPointerMove = this.onPointerMove.bind(this);
            this.onPointerUp = this.onPointerUp.bind(this);
            this.onKeyDown = this.onKeyDown.bind(this);

            this.handle.addEventListener('pointerdown', this.onPointerDown);
            container.addEventListener('pointerdown', this.onPointerDown);
            this.handle.addEventListener('keydown', this.onKeyDown);
        },

        onPointerDown: function (e) {
            this.active = true;
            this.updateFromEvent(e);

            // Capture pointer for smooth dragging even if finger/mouse leaves container
            try {
                if (e.target && e.target.setPointerCapture) {
                    e.target.setPointerCapture(e.pointerId);
                }
            } catch (err) {}

            window.addEventListener('pointermove', this.onPointerMove, { passive: true });
            window.addEventListener('pointerup', this.onPointerUp);
            window.addEventListener('pointercancel', this.onPointerUp);
        },

        onPointerMove: function (e) {
            if (!this.active) return;
            this.updateFromEvent(e);
        },

        onPointerUp: function (e) {
            this.active = false;
            window.removeEventListener('pointermove', this.onPointerMove);
            window.removeEventListener('pointerup', this.onPointerUp);
            window.removeEventListener('pointercancel', this.onPointerUp);
        },

        updateFromEvent: function (e) {
            if (!this.container) return;
            const rect = this.container.getBoundingClientRect();
            const clientX = e.clientX;
            let percent = ((clientX - rect.left) / rect.width) * 100;
            percent = Math.max(0, Math.min(100, percent));
            this.setPosition(percent);
        },

        onKeyDown: function (e) {
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                this.setPosition(Math.max(0, this.currentPercent - 5));
            } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                this.setPosition(Math.min(100, this.currentPercent + 5));
            } else if (e.key === 'Home') {
                e.preventDefault();
                this.setPosition(0);
            } else if (e.key === 'End') {
                e.preventDefault();
                this.setPosition(100);
            }
        },

        setPosition: function (percent) {
            this.currentPercent = Math.round(percent * 10) / 10;
            if (this.handle) {
                this.handle.style.left = `${this.currentPercent}%`;
                this.handle.setAttribute('aria-valuenow', Math.round(this.currentPercent));
            }
            if (this.afterImageWrap) {
                this.afterImageWrap.style.clipPath = `polygon(${this.currentPercent}% 0, 100% 0, 100% 100%, ${this.currentPercent}% 100%)`;
            }
        },

        destroy: function () {
            this.active = false;
            if (this.handle) {
                this.handle.removeEventListener('pointerdown', this.onPointerDown);
                this.handle.removeEventListener('keydown', this.onKeyDown);
            }
            if (this.container) {
                this.container.removeEventListener('pointerdown', this.onPointerDown);
            }
            window.removeEventListener('pointermove', this.onPointerMove);
            window.removeEventListener('pointerup', this.onPointerUp);
            window.removeEventListener('pointercancel', this.onPointerUp);
        }
    };
})();
