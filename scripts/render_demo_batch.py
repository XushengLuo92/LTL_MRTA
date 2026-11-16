"""Validate and render saved planner replays into a shareable demo collection."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import imageio_ffmpeg
from PIL import Image
from mrta.demo import load_replay
from mrta.trace_check import validate_replay
from mrta.vis import Trajectory


def render(case, folder):
    replay = folder / f'case_{case:02d}.json'
    workspace, paths, times, _, data = load_replay(replay)
    trajectory = Trajectory(paths, times)
    validation = validate_replay(workspace, trajectory, data['mission'])
    replay.with_suffix('.validation.json').write_text(json.dumps(validation, indent=2)+'\n')
    if not validation['motion_valid'] or not validation['ltl_satisfied_on_repeating_cycle']:
        raise RuntimeError(f'Case {case} failed replay validation.')
    video, poster, gif = [replay.with_suffix(s) for s in ('.mp4','.png','.gif')]
    command = [sys.executable, '-m', 'mrta.demo', '--replay', str(replay)]
    subprocess.run(command+['--output',str(video),'--fps','30','--dpi','120'],check=True,cwd=ROOT,capture_output=True,text=True)
    subprocess.run(command+['--output',str(poster),'--step',str(trajectory.horizon//3)],check=True,cwd=ROOT,capture_output=True,text=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory(prefix='mrta-palette-') as temp:
        palette = str(Path(temp)/'palette.png')
        subprocess.run([ffmpeg,'-loglevel','error','-y','-i',str(video),'-vf',
                        'fps=12,scale=960:-1:flags=lanczos,palettegen=stats_mode=diff',
                        '-frames:v','1',palette],check=True,capture_output=True,text=True)
        subprocess.run([ffmpeg,'-loglevel','error','-y','-i',str(video),'-i',palette,'-lavfi',
                        'fps=12,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3',
                        '-loop','0',str(gif)],check=True,capture_output=True,text=True)
    frames = imageio_ffmpeg.read_frames(str(video),pix_fmt='rgb24')
    metadata = next(frames)
    count = sum(1 for _ in frames)
    if metadata['size'] != (1920,1080) or count != max(2,math.ceil(trajectory.horizon/2*30)+1):
        raise RuntimeError(f'Case {case} video failed frame verification.')
    with Image.open(gif) as preview:
        if preview.size != (960,540) or preview.n_frames < 2:
            raise RuntimeError(f'Case {case} GIF failed verification.')
    return {'case':case,'video':video.name,'gif':gif.name,'poster':poster.name,'replay':replay.name,
            'horizon':trajectory.horizon,'robot_count':len(paths),'video_frames':count,'fps':30,
            'validation':replay.with_suffix('.validation.json').name,'motion_valid':True,'ltl_valid':True,
            'replay_sha256':hashlib.sha256(replay.read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',type=int,nargs='+',default=list(range(2,11)))
    parser.add_argument('--output-dir',type=Path,default=ROOT/'data/all_cases')
    parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args()
    manifest=args.output_dir/'rendered.json'
    rows={row['case']:row for row in json.loads(manifest.read_text())} if manifest.exists() else {}
    failures=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(render,case,args.output_dir):case for case in args.cases}
        for job in as_completed(jobs):
            case=jobs[job]
            try:
                row=job.result();rows[case]=row
                print(f'Case {case}: video, GIF, poster, replay verified.',flush=True)
            except Exception as error:
                detail = getattr(error, 'stderr', '') or str(error)
                failures.append({'case':case,'error':detail})
                print(f'Case {case}: {detail}',flush=True)
            manifest.write_text(json.dumps(sorted(rows.values(),key=lambda row:row['case']),indent=2)+'\n')
    (args.output_dir/'render-errors.json').write_text(json.dumps(failures,indent=2)+'\n')
    return int(bool(failures))


if __name__=='__main__':
    raise SystemExit(main())
