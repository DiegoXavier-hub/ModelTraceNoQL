"use client";

interface SkeletonProps {
  variant?: "text" | "box" | "circle";
  width?: number | string;
  height?: number | string;
  count?: number;
}

export function Skeleton({ variant = "text", width, height, count = 1 }: SkeletonProps) {
  const className = `skeleton ${variant}`;
  const items = Array.from({ length: count }, (_, index) => index);
  return (
    <>
      {items.map((index) => (
        <span
          key={index}
          className={className}
          style={{
            width: width ?? undefined,
            height: height ?? undefined
          }}
        />
      ))}
    </>
  );
}
