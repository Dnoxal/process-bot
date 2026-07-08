import React, { useEffect, useRef } from "react";

function createStars(width, height, count) {
  return Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.16,
    vy: (Math.random() - 0.5) * 0.16,
    size: Math.random() * 1.7 + 0.45,
    alpha: Math.random() * 0.58 + 0.24,
  }));
}

export function GravityStarsBackground({
  className = "",
  starColor = "#D4AF37",
  density = 135,
  gravity = 0.028,
  range = 240,
  pointerEvents = true,
  ...props
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;

    const context = canvas.getContext("2d");
    const pointer = { x: 0, y: 0, active: false };
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let animationFrame = 0;
    let stars = [];
    let width = 0;
    let height = 0;

    function resize() {
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      width = canvas.offsetWidth || window.innerWidth;
      height = canvas.offsetHeight || window.innerHeight;
      canvas.width = Math.floor(width * ratio);
      canvas.height = Math.floor(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      stars = createStars(width, height, Math.max(72, Math.round((width * height * density) / 1_000_000)));
    }

    function draw() {
      context.clearRect(0, 0, width, height);

      for (const star of stars) {
        if (!reducedMotion) {
          if (pointerEvents && pointer.active) {
            const dx = pointer.x - star.x;
            const dy = pointer.y - star.y;
            const distance = Math.hypot(dx, dy);
            if (distance > 0 && distance < range) {
              const force = (1 - distance / range) * gravity;
              star.vx += (dx / distance) * force;
              star.vy += (dy / distance) * force;
            }
          }

          star.vx *= 0.986;
          star.vy *= 0.986;
          star.x += star.vx;
          star.y += star.vy;

          if (star.x < -8) star.x = width + 8;
          if (star.x > width + 8) star.x = -8;
          if (star.y < -8) star.y = height + 8;
          if (star.y > height + 8) star.y = -8;
        }

        context.beginPath();
        context.globalAlpha = star.alpha;
        context.fillStyle = starColor;
        context.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        context.fill();
      }

      context.globalAlpha = 1;
      if (!reducedMotion) {
        animationFrame = window.requestAnimationFrame(draw);
      }
    }

    function handlePointerMove(event) {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      pointer.active = true;
    }

    function handlePointerLeave() {
      pointer.active = false;
    }

    resize();
    draw();
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerleave", handlePointerLeave);

    return () => {
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerleave", handlePointerLeave);
    };
  }, [density, gravity, pointerEvents, range, starColor]);

  return (
    <canvas
      ref={canvasRef}
      className={`gravity-stars-background ${className}`.trim()}
      aria-hidden="true"
      {...props}
    />
  );
}
