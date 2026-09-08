/**
 * Campus Issue Portal - Client-side Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile Sidebar Toggle & Off-Canvas Navigation
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
  const sidebar = document.querySelector('.app-sidebar');
  const backdrop = document.getElementById('sidebarBackdrop');

  const closeSidebar = () => {
    if (sidebar) sidebar.classList.remove('show');
    if (backdrop) backdrop.classList.remove('show');
  };

  const openSidebar = () => {
    if (sidebar) sidebar.classList.add('show');
    if (backdrop) backdrop.classList.add('show');
  };

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      if (sidebar.classList.contains('show')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', closeSidebar);
  }

  if (backdrop) {
    backdrop.addEventListener('click', closeSidebar);
  }

  // Close sidebar on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('show')) {
      closeSidebar();
    }
  });

  // Public Landing Page Navbar Scroll Transformation (Glass effect)
  const publicNavbar = document.querySelector('.mvgr-public-navbar');
  if (publicNavbar) {
    let ticking = false;
    const updateNavbarOnScroll = () => {
      if (window.scrollY > 20) {
        publicNavbar.classList.add('navbar-scrolled');
      } else {
        publicNavbar.classList.remove('navbar-scrolled');
      }
      ticking = false;
    };

    window.addEventListener('scroll', () => {
      if (!ticking) {
        window.requestAnimationFrame(updateNavbarOnScroll);
        ticking = true;
      }
    }, { passive: true });

    // Initial check on load
    updateNavbarOnScroll();
  }

  // Public Landing Page Navbar Mobile Auto-Close
  const publicNavbarCollapse = document.getElementById('mvgrNav');
  if (publicNavbarCollapse) {
    const navLinks = publicNavbarCollapse.querySelectorAll('.nav-link, .btn, .mvgr-nav-btn-login, .mvgr-nav-btn-register');
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth < 992 && typeof bootstrap !== 'undefined') {
          const bsCollapse = bootstrap.Collapse.getInstance(publicNavbarCollapse);
          if (bsCollapse) {
            bsCollapse.hide();
          }
        }
      });
    });
  }

  // Password visibility toggle
  document.querySelectorAll('.toggle-password').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        const isPassword = input.getAttribute('type') === 'password';
        input.setAttribute('type', isPassword ? 'text' : 'password');
        btn.innerHTML = isPassword ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
      }
    });
  });

  // Star rating hover text updater
  const starInputs = document.querySelectorAll('.star-rating input');
  const ratingText = document.getElementById('ratingLabelText');
  const ratingLabels = {
    '1': '1 Star - Very Unsatisfied',
    '2': '2 Stars - Unsatisfied',
    '3': '3 Stars - Neutral',
    '4': '4 Stars - Satisfied',
    '5': '5 Stars - Highly Satisfied'
  };

  starInputs.forEach(radio => {
    radio.addEventListener('change', (e) => {
      if (ratingText) {
        ratingText.textContent = ratingLabels[e.target.value] || '';
      }
    });
  });
});
