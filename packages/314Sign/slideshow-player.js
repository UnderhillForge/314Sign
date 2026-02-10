/**
 * Slideshow Playback Module for 314Sign Kiosk
 * Uses Splide.js for carousel and custom per-slide duration logic
 */

// Override slideshow functions in main index.html
window.initializeSlideshowModule = function() {
  // Check if URL has slideshow parameter
  window.checkForSlideshow = function() {
    const urlParams = new URLSearchParams(window.location.search);
    const slideshowName = urlParams.get('slideshow');
    
    if (slideshowName) {
      window.loadSlideshow(slideshowName);
    }
  };

  // Load slideshow from database API
  window.loadSlideshow = function(slideshowName) {
    // Extract name if it's a full path
    if (slideshowName && slideshowName.includes('/')) {
      slideshowName = slideshowName.split('/').pop().replace('.json', '');
    }

    fetch('/api/slideshows/' + slideshowName)
      .then(r => r.ok ? r.json() : null)
      .then(response => response ? response.data : null)
      .then(data => {
        if (data && data.slides && data.slides.length > 0) {
          window.slideshowData = data;
          window.isPlayingSlideshow = true;
          if (typeof window.updateQrVisibility === 'function') {
            window.updateQrVisibility();
          }

          // Hide header and clock
          if (window.headerEl) window.headerEl.style.display = 'none';
          if (window.clockEl) window.clockEl.style.display = 'none';
          if (window.specialsDiv) window.specialsDiv.style.display = 'none';

          // Initialize Splide carousel
          window.initializeSlideshowPlayer();
        }
      })
      .catch(err => {
        console.error('Failed to load slideshow:', err);
          window.isPlayingSlideshow = false;
          if (typeof window.updateQrVisibility === 'function') {
            window.updateQrVisibility();
          }
      });
  };

  // Initialize Splide for slideshow  
  window.initializeSlideshowPlayer = function() {
    if (!window.slideshowData || !window.slideshowData.slides || window.slideshowData.slides.length === 0) {
      return;
    }

    // Create Splide carousel HTML
    window.specialsDiv.innerHTML = `<div class="splide" id="slideshow-carousel" role="region">
      <div class="splide__track">
        <ul class="splide__list">
          ${window.slideshowData.slides.map((slide, i) => `
            <li class="splide__slide" data-index="${i}" style="display:flex;align-items:center;justify-content:center;">
              <div class="slide-content" style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;position:relative;">
                ${window.renderSlideContent(slide)}
              </div>
            </li>
          `).join('')}
        </ul>
      </div>
    </div>`;

    window.specialsDiv.style.display = 'flex';

    // Initialize Splide with disabled autoplay (we'll handle timing manually)
    const splide = new Splide('#slideshow-carousel', {
      type: 'fade',
      rewind: true,
      autoplay: false,
      drag: false,
      keyboard: false,
      wheel: false,
      arrows: false,
      pagination: false,
      speed: 800,
      direction: 'ltr'
    });

    splide.on('mounted', () => {
      window.advanceToNextSlide(splide);
    });

    splide.mount();
    window.currentSplide = splide;
  };

  // Render slide content (image or text)
  window.renderSlideContent = function(slide) {
    if (slide.type === 'image') {
      let html = `<img src="${slide.media}" style="max-width:100%;max-height:100%;object-fit:contain;" alt="Slide">`;
      if (slide.caption) {
        const pos = slide.captionPosition || 'bottom';
        const top = pos === 'top' ? '0' : pos === 'center' ? '50%' : 'auto';
        const bottom = pos === 'bottom' ? '0' : 'auto';
        const transform = pos === 'center' ? 'translateY(-50%)' : 'none';
        const topStyle = top && top !== 'auto' ? `top:${top};` : '';
        const bottomStyle = bottom && bottom !== 'auto' ? `bottom:${bottom};` : '';
        html += `<div style="position:absolute;${topStyle}${bottomStyle}width:100%;padding:1rem 2rem;background:rgba(0,0,0,0.7);color:white;text-align:center;font-size:clamp(1rem,3vw,2.5rem);transform:${transform};">${slide.caption}</div>`;
      }
      return html;
    } else if (slide.type === 'text') {
      return `<div style="max-width:90%;text-align:center;color:white;padding:2rem;font-family:${slide.font || 'Lato, sans-serif'};font-size:${slide.fontSize || 5}vw;">${window.renderMarkdownWithColorTags(slide.content || '')}</div>`;
    }
    return '';
  };

  // Helper to render markdown with color tag support
  window.renderMarkdownWithColorTags = function(content) {
    const colorMap = {
      r: '#ff4444', y: '#ffdd44', g: '#44ff44', b: '#4488ff',
      o: '#ff8844', p: '#ff44ff', w: '#ffffff'
    };
    
    let processed = content;
    Object.keys(colorMap).forEach(colorKey => {
      const color = colorMap[colorKey];
      const regex = new RegExp('\\{' + colorKey + '\\}', 'g');
      processed = processed.replace(regex, `<span style="color:${color};">`);
    });
    processed = processed.replace(/\{\/[a-z]\}/g, '</span>');
    
    try {
      return window.marked ? window.marked.parse(processed) : processed;
    } catch (e) {
      console.warn('Markdown parse error:', e);
      return processed;
    }
  };

  // Advance to next slide with custom per-slide duration
  window.advanceToNextSlide = function(splide) {
    if (!window.slideshowData || !window.slideshowData.slides) return;

    const currentSlide = window.slideshowData.slides[splide.index];
    const duration = currentSlide.duration || window.slideshowData.defaultDuration || 5000;

    // Clear previous timeout
    if (window.slideTimeout) clearTimeout(window.slideTimeout);

    // Schedule next slide
    window.slideTimeout = setTimeout(() => {
      splide.go('+');
      window.advanceToNextSlide(splide);
    }, duration);
  };

  // Load slideshow from rule
  window.loadSlideshowFromRule = function(slideshowPath) {
    if (!slideshowPath) return;
    if (window.isPlayingSlideshow) return;
    window.loadSlideshow(slideshowPath);
  };

  // Next slide (for backward compatibility)
  window.nextSlide = function() {
    if (window.currentSplide) {
      window.currentSplide.go('+');
    }
  };

  // Cleanup slideshow
  window.cleanupSlideshow = function() {
    if (window.slideTimeout) clearTimeout(window.slideTimeout);
    if (window.currentSplide) {
      window.currentSplide.destroy();
      window.currentSplide = null;
    }
    window.isPlayingSlideshow = false;
    if (typeof window.updateQrVisibility === 'function') {
      window.updateQrVisibility();
    }
  };
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', window.initializeSlideshowModule);
} else {
  window.initializeSlideshowModule();
}
