enum DetectorState {
  WAITING,
  FOUND,
  TRACKING,
  LOST
};

class ContinuousDetector {
  public:
    ContinuousDetector(int _findDelay = 500, int loseDelay = 500);
    int findDelay, loseDelay;
    DetectorState state;

    void reset();
    DetectorState tick(bool value);
  private:
    DetectorState tickInternal(bool value);
    unsigned long found, lost;
    bool isTracking;
};