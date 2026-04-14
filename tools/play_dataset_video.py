#!/usr/bin/env python3
"""
Dataset Video Player
Play stereo dataset as video with controls
"""

import cv2
import numpy as np
from pathlib import Path
import time


class DatasetVideoPlayer:
    """Play stereo dataset images as video"""
    
    def __init__(self, left_dir: str, right_dir: str):
        """
        Initialize video player
        
        Args:
            left_dir: Directory containing left camera images
            right_dir: Directory containing right camera images
        """
        self.left_dir = Path(left_dir)
        self.right_dir = Path(right_dir)
        
        # Load image pairs
        self.image_pairs = self.load_image_pairs()
        self.current_frame = 0
        self.total_frames = len(self.image_pairs)
        
        # Playback controls
        self.playing = True
        self.fps = 30  # Frames per second
        self.frame_delay = 1.0 / self.fps
        
        # Display settings
        self.show_stereo = True  # Show both left and right
        self.resize_factor = 0.6  # Resize for display
        
    def load_image_pairs(self):
        """Load and sort image pairs"""
        left_images = sorted([f for f in self.left_dir.glob("*.jpg")])
        right_images = sorted([f for f in self.right_dir.glob("*.jpg")])
        
        pairs = []
        right_dict = {f.name: f for f in right_images}
        
        for left_path in left_images:
            if left_path.name in right_dict:
                pairs.append((left_path, right_dict[left_path.name]))
        
        print(f"Loaded {len(pairs)} stereo image pairs")
        return pairs
    
    def load_frame(self, frame_idx: int):
        """Load a specific frame"""
        if frame_idx < 0 or frame_idx >= self.total_frames:
            return None, None
        
        left_path, right_path = self.image_pairs[frame_idx]
        left_img = cv2.imread(str(left_path))
        right_img = cv2.imread(str(right_path))
        
        return left_img, right_img
    
    def create_display_frame(self, left_img, right_img):
        """Create combined display frame"""
        if left_img is None or right_img is None:
            return None
        
        # Resize for display
        h, w = left_img.shape[:2]
        new_w = int(w * self.resize_factor)
        new_h = int(h * self.resize_factor)
        
        left_resized = cv2.resize(left_img, (new_w, new_h))
        right_resized = cv2.resize(right_img, (new_w, new_h))
        
        if self.show_stereo:
            # Side-by-side display
            display = np.hstack([left_resized, right_resized])
            
            # Add labels
            cv2.putText(display, "LEFT", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display, "RIGHT", (new_w + 10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            # Show only left
            display = left_resized
        
        # Add info overlay
        info_text = f"Frame: {self.current_frame + 1}/{self.total_frames} | FPS: {self.fps}"
        status = "PLAYING" if self.playing else "PAUSED"
        
        # Add semi-transparent background for text
        overlay = display.copy()
        cv2.rectangle(overlay, (0, display.shape[0] - 80), 
                     (display.shape[1], display.shape[0]), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, display, 0.5, 0, display)
        
        # Add text
        cv2.putText(display, info_text, (10, display.shape[0] - 45), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display, f"Status: {status}", (10, display.shape[0] - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if self.playing else (0, 0, 255), 2)
        
        # Add progress bar
        progress = int((self.current_frame / self.total_frames) * display.shape[1])
        cv2.rectangle(display, (0, display.shape[0] - 5), 
                     (progress, display.shape[0]), (0, 255, 0), -1)
        
        return display
    
    def play(self):
        """Play the dataset as video"""
        print("\n" + "="*70)
        print("DATASET VIDEO PLAYER")
        print("="*70)
        print(f"Total frames: {self.total_frames}")
        print(f"FPS: {self.fps}")
        print("\nControls:")
        print("  SPACE    - Play/Pause")
        print("  →/←      - Next/Previous frame")
        print("  +/-      - Increase/Decrease speed")
        print("  S        - Toggle stereo/single view")
        print("  R        - Restart from beginning")
        print("  Q/ESC    - Quit")
        print("="*70 + "\n")
        
        cv2.namedWindow('Dataset Video Player', cv2.WINDOW_NORMAL)
        
        last_frame_time = time.time()
        
        while True:
            # Load current frame
            left_img, right_img = self.load_frame(self.current_frame)
            
            if left_img is not None:
                # Create display
                display = self.create_display_frame(left_img, right_img)
                
                if display is not None:
                    cv2.imshow('Dataset Video Player', display)
            
            # Handle keyboard input
            wait_time = 1 if self.playing else 0
            key = cv2.waitKey(wait_time) & 0xFF
            
            if key == ord('q') or key == 27:  # Q or ESC
                print("\nExiting video player...")
                break
            
            elif key == ord(' '):  # SPACE - Play/Pause
                self.playing = not self.playing
                print(f"{'Playing' if self.playing else 'Paused'}")
            
            elif key == 83:  # Right arrow - Next frame
                self.current_frame = min(self.current_frame + 1, self.total_frames - 1)
                print(f"Frame: {self.current_frame + 1}/{self.total_frames}")
            
            elif key == 81:  # Left arrow - Previous frame
                self.current_frame = max(self.current_frame - 1, 0)
                print(f"Frame: {self.current_frame + 1}/{self.total_frames}")
            
            elif key == ord('+') or key == ord('='):  # Increase speed
                self.fps = min(self.fps + 5, 120)
                self.frame_delay = 1.0 / self.fps
                print(f"Speed: {self.fps} FPS")
            
            elif key == ord('-'):  # Decrease speed
                self.fps = max(self.fps - 5, 5)
                self.frame_delay = 1.0 / self.fps
                print(f"Speed: {self.fps} FPS")
            
            elif key == ord('s'):  # Toggle stereo view
                self.show_stereo = not self.show_stereo
                print(f"View: {'Stereo' if self.show_stereo else 'Single'}")
            
            elif key == ord('r'):  # Restart
                self.current_frame = 0
                print("Restarting from beginning...")
            
            # Auto-advance frame if playing
            if self.playing:
                current_time = time.time()
                if current_time - last_frame_time >= self.frame_delay:
                    self.current_frame += 1
                    last_frame_time = current_time
                    
                    # Loop back to start
                    if self.current_frame >= self.total_frames:
                        self.current_frame = 0
                        print("\nReached end - looping back to start...")
        
        cv2.destroyAllWindows()


def main():
    """Main entry point"""
    base_dir = Path(__file__).resolve().parent.parent
    left_dir = base_dir / "app" / "frontend" / "left"
    right_dir = base_dir / "app" / "frontend" / "right"
    
    # Verify directories exist
    if not left_dir.exists():
        print(f"ERROR: Left image directory not found: {left_dir}")
        return
    
    if not right_dir.exists():
        print(f"ERROR: Right image directory not found: {right_dir}")
        return
    
    # Create and run player
    player = DatasetVideoPlayer(
        left_dir=str(left_dir),
        right_dir=str(right_dir)
    )
    
    player.play()


if __name__ == "__main__":
    main()
