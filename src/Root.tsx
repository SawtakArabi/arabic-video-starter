import {Composition} from 'remotion';
import {Ad, type AdProps} from './Video';

const defaults: AdProps = {
  fps: 30,
  width: 1080,
  height: 1920,
  brand: {name: 'LUMA', logo: 'assets/logo.svg', background: '#F3EDE2', ink: '#163B35', accent: '#C66342'},
  scenes: [],
};

export const Root = () => (
  <Composition
    id="ArabicAd"
    component={Ad}
    defaultProps={defaults}
    fps={30}
    width={1080}
    height={1920}
    durationInFrames={1}
    calculateMetadata={({props}) => {
      if (!props.scenes.length) {
        throw new Error('Prepare a config first, then pass --props=build/your-config.json');
      }
      return {
        durationInFrames: props.scenes.reduce((total, scene) => total + scene.durationInFrames, 0),
        fps: props.fps,
        width: props.width,
        height: props.height,
      };
    }}
  />
);
