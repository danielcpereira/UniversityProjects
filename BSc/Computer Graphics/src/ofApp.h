#pragma once

#include "ofMain.h"
#include "cg_extras.h"
#include "cg_drawing_extras.h"
#include "cg_cam_extras.h"


class ofApp : public ofBaseApp{

	public:
		void setup();
		void update();
		void draw();

		void keyPressed(int key);
		void keyReleased(int key);
		void mouseMoved(int x, int y );
		void mouseDragged(int x, int y, int button);
		void mousePressed(int x, int y, int button);
		void mouseReleased(int x, int y, int button);
		void mouseEntered(int x, int y);
		void mouseExited(int x, int y);
		void windowResized(int w, int h);
		void dragEvent(ofDragInfo dragInfo);
		void gotMessage(ofMessage msg);

		// Variaveis para a fruta
		bool fruit;
		GLfloat fruitProgress;
		GLfloat fruitDuration;

		// Funcoes para a fruta
		void generateFruitPosition();
		bool checkCollisionWithFruit();

		// Funcoes para efeitos
		void eatEffect(GLfloat time);
		void wallCollisonEffect(GLfloat time);

		// Speed
		void speedUpdate();
		GLfloat snakeSpeed;

		// Colisoes 
		bool checkSelfCollision();
		bool colliding;
		GLfloat collidingTime, collidingInterval;

		// Eat
		GLfloat eatingDuration;
		bool eating;
		GLfloat temporizador;

		// Explosao
		float explosionTime;
		bool exploding;
		void explodingEffect(GLfloat time);

		// Escalas
		GLfloat modifyScale;
		std::vector<float> scales;
		GLfloat fruitScale;

		// Cores da cobra
		GLint r, g, b;

		// Direcoes
		GLint directionX, directionY;
	
		// Confirmaçao para evitar bug
		GLint verifica;

		// Snake stuff
		void addSnakeUnit();
		void setupSnake();
		void drawSnake();
		std::vector<ofVec3f> snakeBody;

		// Posicao da fruta
		GLfloat fruitPosX, fruitPosY;
		
		// Variavel de tempo
		GLfloat elapsedTime;

		// Camera variables
		GLint view;
		GLfloat lensAngle;
		GLfloat alpha, beta;
		GLfloat perfectDist;
		GLint cameraMode;
		
		// Floor
		GLint resX, resY;
		GLfloat floorWidth, floorHeight, floorHeightPos;

		// Snake
		GLfloat baseWidth, baseDepth, baseHeight;
		GLfloat basePosX, basePosY, basePosZ;

		// Meta 2

		// luzes
		
		bool fruitLight;

		GLfloat ambientLight[4];

		GLfloat pointPos[4];
		GLfloat pointAmb[4];
		GLfloat pointDif[4];
		GLfloat pointSpec[4];

		GLfloat lanternPos[4];
		GLfloat lanternDir[3];
		GLfloat lanternAmb[4];
		GLfloat lanternDif[4];
		GLfloat lanternSpec[4];

		void setupFruitLight();
		void setupLanternLight();
		void setupDirectionalLight();

		bool lanternLight;

		GLfloat lastDirectionX ;
		GLfloat lastDirectionY ;

		//Texturas

		ofImage fieldTexture;
		ofImage snakeTexture;
		ofImage appleTexture;
		ofImage sunTexture;

		//Score

		GLint score;
		GLint highscore;

		bool hardlevel;

		//Sol
		GLfloat cubePosX ;  
		GLfloat cubePosZ;               
		GLfloat cubeSpeed;        
		GLfloat cubeDirection;

		bool sunMoving;

		// Luz Direcional

		GLfloat dirVec[4];
		GLfloat dirAmb[4];
		GLfloat dirDif[4];
		GLfloat dirSpec[4];

		bool dirOn;

		ofVec3f dirVec3f;

		// Gameover
		GLint scoreSaved;
		bool gameover;

		// Componentes da luz
		bool ambientOn;
		bool diffuseOn ;
		bool specularOn ;

};
