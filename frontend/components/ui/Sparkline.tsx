"use client";

interface SparklineProps {
  values: ReadonlyArray<number>;
  width?: number;
  height?: number;
  className?: string;
  ariaLabel?: string;
}

export function Sparkline({
  values,
  width = 80,
  height = 28,
  className = "sparkline",
  ariaLabel
}: SparklineProps) {
  if (!values || values.length < 2) {
    return null;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = width / (values.length - 1);

  const points = values
    .map((value, index) => {
      const x = index * stepX;
      const y = height - ((value - min) / range) * (height - 2) - 1;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" L ");

  const path = `M ${points}`;

  return (
    <svg
      className={className}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      role="img"
      aria-label={ariaLabel ?? "Sparkline"}
    >
      <path d={path} />
    </svg>
  );
}
