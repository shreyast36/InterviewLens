from interviewlens.video_pipeline.capture import synthetic_frames
from interviewlens.video_pipeline.keypoint_processor import normalize_frame, to_array
from interviewlens.video_pipeline.pose_estimation import build_pose_estimator
from interviewlens.video_pipeline.signal_detection import build_signal_detector
from interviewlens.video_pipeline.temporal_sequence import RollingWindowBuilder


def test_pose_estimator_mock_output_shape():
    estimator = build_pose_estimator("rtmpose-s")
    frame, ts = next(synthetic_frames(1))
    pose_frame = normalize_frame(estimator.estimate(frame, 0, ts))
    arr = to_array(pose_frame)
    assert arr.shape == (11, 3)


def test_rolling_window_emits_after_fill():
    builder = RollingWindowBuilder(fps=4, window_seconds=1, stride_seconds=1)
    estimator = build_pose_estimator("rtmpose-s")
    windows = []
    for i, (frame, ts) in enumerate(synthetic_frames(8, fps=4)):
        pose_frame = normalize_frame(estimator.estimate(frame, i, ts))
        w = builder.push(pose_frame)
        if w:
            windows.append(w)
    assert len(windows) >= 1


def test_signal_detector_returns_list():
    detector = build_signal_detector("champion")
    builder = RollingWindowBuilder(fps=4, window_seconds=1, stride_seconds=1)
    estimator = build_pose_estimator("rtmpose-s")
    window = None
    for i, (frame, ts) in enumerate(synthetic_frames(8, fps=4)):
        pose_frame = normalize_frame(estimator.estimate(frame, i, ts))
        window = builder.push(pose_frame) or window
    assert isinstance(detector.detect(window), list)
