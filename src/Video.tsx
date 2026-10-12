import {loadFont} from '@remotion/fonts';
import {Audio} from '@remotion/media';
import {AbsoluteFill, Img, Series, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';

// The OFL font files are copied from the pinned Fontsource package by prepare.py.
for (const weight of ['500', '700']) {
  for (const subset of ['arabic', 'latin']) {
    loadFont({
      family: `Noto ${subset}`,
      url: staticFile(`fonts/noto-sans-arabic-${subset}-${weight}-normal.woff2`),
      weight,
    });
  }
}

type Scene = {
  id: string;
  title: string;
  caption: string;
  image: string;
  audio: string;
  audioStartFrame: number;
  durationInFrames: number;
};

export type AdProps = {
  fps: number;
  width: number;
  height: number;
  brand: {name: string; category?: string; logo: string; background: string; ink: string; accent: string};
  scenes: Scene[];
  notice?: string;
};

const SceneCard = ({scene, brand, index, count, notice}: {
  scene: Scene; brand: AdProps['brand']; index: number; count: number; notice?: string;
}) => {
  const frame = useCurrentFrame();
  const entrance = interpolate(frame, [0, 12], [24, 0], {extrapolateRight: 'clamp'});
  const scale = interpolate(frame, [0, scene.durationInFrames], [1, 1.035]);
  return (
    <AbsoluteFill style={{background: brand.background, color: brand.ink, fontFamily: '"Noto arabic", "Noto latin", sans-serif', padding: 80}}>
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
        <Img src={staticFile(brand.logo)} style={{width: 180, height: 64, objectFit: 'contain'}} />
        <span dir="ltr" style={{fontSize: 26, letterSpacing: 4}}>{brand.category || 'EVERYDAY / OBJECTS'}</span>
      </div>
      <div style={{marginTop: 88, transform: `translateY(${entrance}px)`}} dir="rtl" lang="ar">
        <div style={{fontSize: 24, color: brand.accent, fontWeight: 700, marginBottom: 28}}>{brand.name}</div>
        <h1 data-copy style={{margin: 0, fontWeight: 700, fontSize: 88, lineHeight: 1.6, textAlign: 'right', overflowWrap: 'break-word', whiteSpace: 'pre-wrap'}}>{scene.title}</h1>
      </div>
      <div style={{height: 690, flexShrink: 0, margin: '40px -20px 24px', overflow: 'hidden', borderRadius: 240, background: '#E7DECB'}}>
        <Img src={staticFile(scene.image)} style={{width: '100%', height: '100%', objectFit: 'contain', transform: `scale(${scale})`}} />
      </div>
      <p data-copy dir="rtl" lang="ar" style={{margin: 0, fontSize: 43, fontWeight: 500, lineHeight: 1.85, textAlign: 'right', overflowWrap: 'break-word', whiteSpace: 'pre-wrap'}}>{scene.caption}</p>
      <div style={{marginTop: 'auto', paddingTop: 28, borderTop: `2px solid ${brand.ink}30`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 24}}>
        <span>{notice || 'LUMA / FICTIONAL PRODUCT CONCEPT'}</span>
        <span dir="ltr">{String(index + 1).padStart(2, '0')} / {String(count).padStart(2, '0')}</span>
      </div>
      <Sequence from={scene.audioStartFrame} layout="none">
        <Audio src={staticFile(scene.audio)} onError={() => 'fail'} />
      </Sequence>
    </AbsoluteFill>
  );
};

export const Ad = ({scenes, brand, notice}: AdProps) => (
  <Series>
    {scenes.map((scene, index) => (
      <Series.Sequence key={scene.id} durationInFrames={scene.durationInFrames} name={scene.id}>
        <SceneCard scene={scene} brand={brand} index={index} count={scenes.length} notice={notice} />
      </Series.Sequence>
    ))}
  </Series>
);
