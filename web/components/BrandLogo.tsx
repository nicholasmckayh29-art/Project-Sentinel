"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

const LOGO_SRC = "/logo.png";
/** Source image is 1024×558 */
const LOGO_ASPECT = 1024 / 558;

type BrandLogoProps = {
  href?: string;
  /** Render height in px; width follows logo aspect ratio */
  height?: number;
  /** Extra text beside logo (off by default — artwork includes PROJECT SENTINEL) */
  showWordmark?: boolean;
  className?: string;
};

export function BrandLogo({
  href = "/",
  height = 32,
  showWordmark = false,
  className = "",
}: BrandLogoProps) {
  const [imgError, setImgError] = useState(false);
  const width = Math.round(height * LOGO_ASPECT);

  const inner = (
    <>
      {!imgError && (
        <Image
          src={LOGO_SRC}
          alt="Project Sentinel"
          width={width}
          height={height}
          className="object-contain shrink-0"
          priority
          onError={() => setImgError(true)}
        />
      )}
      {(showWordmark || imgError) && (
        <span className="font-mono text-accent terminal-glow text-sm tracking-widest">
          PROJECT SENTINEL
        </span>
      )}
    </>
  );

  const classes = `inline-flex items-center gap-2.5 ${className}`;

  if (href) {
    return (
      <Link href={href} className={`${classes} hover:opacity-90 transition-opacity`}>
        {inner}
      </Link>
    );
  }

  return <span className={classes}>{inner}</span>;
}
