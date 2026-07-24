import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

// Transparent Instagram-story chrome: progress bar, username header, animated like-heart.
// Render to alpha webm, then ffmpeg-overlay onto b-roll.
export const InstagramStory: React.FC<{
  username: string; timeAgo: string; storySeconds: number; likes: number;
}> = ({ username, timeAgo, storySeconds, likes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fadeIn = interpolate(frame, [0, fps * 0.3], [0, 1], { extrapolateRight: "clamp" });
  const progress = Math.min(100, (frame / (fps * storySeconds)) * 100);
  // like-heart pops at t=1s with ease-out-back overshoot
  const heartPop = spring({ frame: frame - fps, fps, config: { damping: 9, mass: 0.6 } });
  const heartScale = frame > fps ? 0.6 + heartPop * 0.5 : 0;

  return (
    <AbsoluteFill style={{ opacity: fadeIn, fontFamily: "Arial, sans-serif" }}>
      {/* story progress bar */}
      <div style={{ position: "absolute", top: 24, left: 16, right: 16, height: 4, background: "rgba(255,255,255,0.35)", borderRadius: 4 }}>
        <div style={{ height: "100%", width: `${progress}%`, background: "white", borderRadius: 4 }} />
      </div>
      {/* username header */}
      <div style={{ position: "absolute", top: 48, left: 20, display: "flex", alignItems: "center", gap: 14, color: "white", fontWeight: 700 }}>
        <div style={{ width: 56, height: 56, borderRadius: "50%", padding: 3, background: "linear-gradient(45deg,#f09433,#dc2743,#bc1888)" }}>
          <div style={{ width: "100%", height: "100%", borderRadius: "50%", background: "#222" }} />
        </div>
        <span style={{ fontSize: 30 }}>{username}</span>
        <span style={{ fontSize: 24, opacity: 0.7 }}>{timeAgo}</span>
        <span style={{ position: "absolute", right: 20, fontSize: 40 }}>×</span>
      </div>
      {/* animated like-heart bottom-right */}
      <div style={{ position: "absolute", bottom: 220, right: 36, transform: `scale(${heartScale})`, fontSize: 80 }}>❤️</div>
      {/* likes counter */}
      {likes > 0 && (
        <div style={{ position: "absolute", bottom: 150, left: 36, color: "white", fontWeight: 700, fontSize: 30 }}>
          {Math.floor(interpolate(frame, [fps, fps * 4], [0, likes], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })).toLocaleString()} likes
        </div>
      )}
    </AbsoluteFill>
  );
};
