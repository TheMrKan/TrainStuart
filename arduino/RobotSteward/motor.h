enum Type {
  FL, FR, BL, BR, ALL
};

enum Direction {
  F, B, S
};

enum Move {
  Forward, Backward, Right, Left, Stop, Rotate
};

class motor {
  public:
    motor();
    void begin();
    void tick();
    void setSpeed(int speed, Type type);
    void run(int x, int y);
    void go(Move _move);
    bool getState(char axis);

    void clearState();
    void setCurrentPosition(int x, int y);
  private:
    Move move, dir;
    void motor_run(Type motor, Direction dir);
    
    bool moveLoopRunning = false;
    unsigned long tmr;
    unsigned long targetTime;

    int currentX = 0, currentY = 0;
    int targetX, targetY;
    int startX, startY;

    bool completeX = false, completeY = false;

    float SPEED = 215 / 12;
};