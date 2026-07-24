import React from "react";
import { Composition } from "remotion";
import { InstagramStory } from "./InstagramChrome";
import { TelegramForward } from "./TelegramBubble";

// 9:16 1080x1920, 30fps. Duration set per render via --frames or here (default 15s).
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="InstagramStory"
        component={InstagramStory}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{ username: "@yourchannel", timeAgo: "2h", storySeconds: 15, likes: 0 }}
      />
      <Composition
        id="TelegramForward"
        component={TelegramForward}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{ name: "Your Name", text: "Смотрите новый выпуск!", time: "14:32" }}
      />
    </>
  );
};
