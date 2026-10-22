"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { Icon } from "./ui";

const scenes = [
  { src: "/civic-infrastructure-hero.jpg", alt: "Rural Kenyan road, water point, and community" },
  { src: "/kenya-community-nairobi.png", alt: "Residents walking through a Nairobi neighborhood" },
  { src: "/kenya-community-coast.png", alt: "Coastal residents meeting with a community health worker" },
  { src: "/kenya-community-highlands.png", alt: "Highland farmers gathered beside an irrigation channel" },
];

export function HeroCarousel() {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (paused || prefersReducedMotion.matches) return;

    const timer = window.setInterval(() => {
      setActive((current) => (current + 1) % scenes.length);
    }, 7000);

    return () => window.clearInterval(timer);
  }, [paused]);

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
      <div className="hero-carousel__controls" role="group" aria-label="Hero image controls">
        {scenes.map((scene, index) => (
          <button
            key={scene.src}
            className={`hero-carousel__dot ${index === active ? "is-active" : ""}`}
            type="button"
            aria-label={`Show image ${index + 1}: ${scene.alt}`}
            aria-pressed={index === active}
            onClick={() => setActive(index)}
          />
        ))}
        <button
          className="hero-carousel__pause"
          type="button"
          aria-label={paused ? "Resume hero image rotation" : "Pause hero image rotation"}
          title={paused ? "Resume slideshow" : "Pause slideshow"}
          onClick={() => setPaused((current) => !current)}
        >
          <Icon name={paused ? "play" : "pause"} size={13} />
        </button>
      </div>
    </div>
  );
}
