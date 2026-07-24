import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

// Transparent Telegram forward/message bubble that slides up. Composite over b-roll.
export const TelegramForward: React.FC<{ name: string; text: string; time: string }> = ({ name, text, time }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 14, mass: 0.7 } });
  const y = interpolate(enter, [0, 1], [120, 0]);
  const opacity = interpolate(frame, [0, fps * 0.25], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: "Segoe UI, Arial, sans-serif", justifyContent: "flex-end", paddingBottom: 200 }}>
      <div style={{ opacity, transform: `translateY(${y}px)`, margin: "0 40px", background: "rgba(33,33,33,0.92)", borderLeft: "5px solid #5288C1", borderRadius: 14, padding: "22px 26px" }}>
        <div style={{ color: "#5288C1", fontWeight: 700, fontSize: 28, marginBottom: 6 }}>{name}</div>
        <div style={{ color: "white", fontSize: 34, lineHeight: 1.25 }}>{text}</div>
        <div style={{ color: "#8a8a8a", fontSize: 22, textAlign: "right", marginTop: 8 }}>{time}</div>
      </div>
    </AbsoluteFill>
  );
};
