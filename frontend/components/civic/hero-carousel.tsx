"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

const scenes = [
  { src: "/civic-infrastructure-hero.jpg" },
  { src: "/kenya-community-nairobi.png" },
  { src: "/kenya-community-coast.png" },
  { src: "/kenya-community-highlands.png" },
];

export function HeroCarousel() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (prefersReducedMotion.matches) return;

    const timer = window.setInterval(() => {
      setActive((current) => (current + 1) % scenes.length);
    }, 7000);

    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="hero-section__backdrop">
      <div className="hero-carousel__visual" aria-hidden="true">
        {scenes.map((scene, index) => (
          <div className={`hero-carousel__slide ${index === active ? "is-active" : ""}`} key={scene.src}>
            <Image
              src={scene.src}
              alt=""
              className="hero-section__image"
              fill
              priority={index === 0}
              sizes="100vw"
            />
          </div>
        ))}
        <div className="hero-section__overlay" />
      </div>
    </div>
  );
}
