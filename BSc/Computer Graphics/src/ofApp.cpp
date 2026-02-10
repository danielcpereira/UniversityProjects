#include "ofApp.h"

#include <cstdlib>  

#include <ctime>    

//--------------------------------------------------------------

void ofApp::setup() {
	//aceleração
	hardlevel = false;

	//pontuação
	score = 0;
	highscore = 0;

	// Configuracoes
	ofSetFrameRate(60);
	glEnable(GL_DEPTH_TEST);

	glPointSize(200);
	glLineWidth(2.5);

	// Perspective
	lensAngle = 67;
	alpha = 10;
	beta = 1000;
	
	// Distancia ideal no lookat
	perfectDist = gh() * 0.5 / tan(lensAngle * 0.5 * PI / 180.);
	
	elapsedTime = 0;

	// Velocidade inicial
	snakeSpeed = 0.15f; 

	// Direcoes 
	int directionX = 0;
	int directionY = 0;

	// Setup
	setupSnake();
	generateFruitPosition();
	snakeBody.clear();
	snakeBody.push_back(ofVec3f(basePosX, basePosY, basePosZ));

	// Primeira camera ativa
	cameraMode = 0;

	// Cor da cobra
	r = 0; g = 215; b = 0;

	// Variaveis do eatingEffect
	eating = 0;
	modifyScale = 1.0f;
	eatingDuration = 1.0f; 
	temporizador = 0.0f;

	// Variaveis do collidingEffect na parede
	colliding = 0;
	collidingTime = 0.0f;
	collidingInterval = 0.05f;

	// Variaveis de explosao
	exploding = false;
	explosionTime = 0.0f;
	 
	// Variaveis da fruta
	fruit = false;
	fruitProgress = 0.0f;
	fruitScale = 0.0f;

	// Variaveis das luzes 
	fruitLight = true;
	lastDirectionX = 0.0f;
	lastDirectionY = -1.0f;

	// Texturas
	snakeTexture.load("snake2.jpg");
	fieldTexture.load("padrao.jpg");
	appleTexture.load("apple.jpg");
	sunTexture.load("sol1.jpg");

	// Variavies do Sol
	cubePosX = -floorWidth * 0.5;  
	cubePosZ = 0.0f;               
	cubeSpeed = .75f;              
	cubeDirection = 1.0f;
	sunMoving = false;
	dirOn = false;
	
	// Gameover 
	gameover = false;

	// Componentes da Luz
	ambientOn = true;
	diffuseOn = true;
	specularOn = true;
}   

//--------------------------------------------------------------

void ofApp::update() {
	if (score > highscore) {
		highscore = score;
	}

	GLfloat time = ofGetLastFrameTime();
	elapsedTime += time;

	// Movimento do Sol
	if (sunMoving) {
		cubePosX += cubeDirection * cubeSpeed;

		cubePosZ = gh() * 0.25 * cos(cubePosX * PI / gh()) * 1.25;

		// Direcao para a esquerda
		if (cubePosX > floorWidth * 0.5) {
			cubeDirection = -1.0f;
		}
		// Direcao para a direita
		else if (cubePosX < -floorWidth * 0.5) {
			cubeDirection = 1.0f;
		}

		dirVec3f = ofVec3f(cubePosX, 0, cubePosZ) - ofVec3f(0, 0, 0);
	}

	// Atualizar a escala da fruta se for menor do que 1.0f
	if (fruitScale < 1.0f) {
		fruitDuration = 1.0f;
		
		if (fruitDuration > 0.0f) {  
			fruitProgress += time / fruitDuration;
		}

		if (fruitProgress > 1.0f) {
			fruitProgress = 1.0f;
		}
		
		fruitScale = fruitProgress;
	}

	if (eating) {
		eatEffect(time);
	}
	
	if (colliding) {
		wallCollisonEffect(time);
		return;
	}

	if (exploding) {
		explodingEffect(time);
		return;  
	}

	if (elapsedTime >= snakeSpeed) { // Metodo para a cobra andar nos quadrados
		verifica = 1;

		int nextPosX = basePosX + directionX;
		int nextPosY = basePosY + directionY;

		// Verificar, antes de tudo, se bate no limite do campo de jogo
		if (nextPosX < 0 || nextPosX >= resX || nextPosY < 0 || nextPosY >= resY) {
			directionX = 0.0f;
			directionY = 0.0f;
			gameover = true;
			colliding = true;
			collidingTime = 0.0f;
			scoreSaved = score;
			score = 0;
			return;
		}
		
		for (int i = snakeBody.size() - 1; i > 0; --i) { // Da ultima ate à primeira posiçao, trocar de posiçao com o seguinte para simular o movimento da cobra
			snakeBody[i] = snakeBody[i - 1];
		}

		snakeBody[0].x += directionX;
		snakeBody[0].y += directionY;

		// Armazenar posição da cabeca
		basePosX += directionX;
		basePosY += directionY;

		// Verificar se comeu a fruta
		if (checkCollisionWithFruit()) {
			speedUpdate();
			generateFruitPosition();
			addSnakeUnit();
			eating = 1;
			score++;
		}

		if (checkSelfCollision()) {
			exploding = true;
			explosionTime = 0.0f;
			gameover = true;
			directionX = 0.0;
			directionY = 0.0;
			scoreSaved = score;
			score = 0;
		}
		elapsedTime = 0;
	}
}

//--------------------------------------------------------------

void ofApp::speedUpdate() {
	// Velocidade que aumenta a cada fruta comida

	// Modo Dificil
	if (hardlevel) {
		snakeSpeed *= 0.92;
	}
	// Modo Facil
	else {
		snakeSpeed *= 0.98;
	}
}

//------------------------------------------------------------------------------------------------------Lights-----------------------------------------------------------------------------

// Luz Pontual
void ofApp::setupFruitLight() {
	glEnable(GL_LIGHTING);
	glEnable(GL_NORMALIZE);
	glEnable(GL_COLOR_MATERIAL);

	glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT);
	glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE);
	glColorMaterial(GL_FRONT_AND_BACK, GL_SPECULAR);
	glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE);

	// Posicoes da Luz
	pointPos[0] = -floorWidth * 0.5 + (fruitPosX * baseWidth) + baseWidth * 0.5;  
	pointPos[1] = floorHeight * 0.5 - (fruitPosY * baseHeight) - baseHeight * 0.5; 
	pointPos[2] = basePosZ + (baseDepth); 
	pointPos[3] = 1.0f;


	// Componente Ambient
	if (ambientOn) {
		pointAmb[0] = 0.0f;
		pointAmb[1] = 0.0f;
		pointAmb[2] = 0.0f;
		pointAmb[3] = 1.0f; // Ligar
	}
	else {
		pointAmb[0] = 0.0f;
		pointAmb[1] = 0.0f;
		pointAmb[2] = 0.0f;
		pointAmb[3] = 0.0f; // Desligar
	}

	// Componente Diffuse
	if (diffuseOn) {
		pointDif[0] = 0.75f;
		pointDif[1] = 0.0f;
		pointDif[2] = 0.0f;
		pointDif[3] = 1.0f; // Ligar
	}
	else {
		pointDif[0] = 0.0f;
		pointDif[1] = 0.0f;
		pointDif[2] = 0.0f;
		pointDif[3] = 0.0f; // Desligar
	}

	// Componente Specular
	if (specularOn) {
		pointSpec[0] = 0.0f;
		pointSpec[1] = 0.0f;
		pointSpec[2] = 0.0f;
		pointSpec[3] = 1.0f; // Ligar
	}
	else {
		pointSpec[0] = 0.0f;
		pointSpec[1] = 0.0f;
		pointSpec[2] = 0.0f;
		pointSpec[3] = 0.0f; // Desligar
	}


	glLightfv(GL_LIGHT1, GL_POSITION, pointPos);
	glLightfv(GL_LIGHT1, GL_AMBIENT, pointAmb);
	glLightfv(GL_LIGHT1, GL_DIFFUSE, pointDif);
	glLightfv(GL_LIGHT1, GL_SPECULAR, pointSpec);

	if (fruitLight) {
		glEnable(GL_LIGHT1);
	}
	else {
		glDisable(GL_LIGHT1);
	}
	
}

// Luz de Foco
void ofApp::setupLanternLight() {
	glEnable(GL_LIGHTING);
	glEnable(GL_NORMALIZE);
	glEnable(GL_COLOR_MATERIAL);

	glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT);
	glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE);
	glColorMaterial(GL_FRONT_AND_BACK, GL_SPECULAR);
	glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE);

	// Abertura da Lanterna
	GLfloat angulo = 22.5f;

	// Posicoes da Luz
	ofVec3f head = snakeBody[0];
	lanternPos[0] = -floorWidth * 0.5 + (head.x * baseWidth) + baseWidth * 0.5;
	lanternPos[1] = floorHeight * 0.5 - (head.y * baseHeight) - baseHeight * 0.5;
	lanternPos[2] = basePosZ + baseDepth;
	lanternPos[3] = 1.0f;

	// Direcao da Luz
	if (directionX == 0.0f && directionY == 0.0f) {
		lanternDir[0] = lastDirectionX;
		lanternDir[1] = -lastDirectionY;
	}
	else {
		lastDirectionX = directionX;
		lastDirectionY = directionY;

		lanternDir[0] = directionX;
		lanternDir[1] = -directionY;
	}
	lanternDir[2] = 0.0f;

	// Componente Ambient
	if (ambientOn) {
		lanternAmb[0] = 0.0f;
		lanternAmb[1] = 0.0f;
		lanternAmb[2] = 0.0f;
		lanternAmb[3] = 1.0f; // Ligar 
	}
	else {
		lanternAmb[0] = 0.0f;
		lanternAmb[1] = 0.0f;
		lanternAmb[2] = 0.0f;
		lanternAmb[3] = 0.0f; // Desligar
	}

	// Componente Diffuse
	if (diffuseOn) {
		lanternDif[0] = 0.25f;
		lanternDif[1] = 0.50f;
		lanternDif[2] = 0.25f;
		lanternDif[3] = 1.0f; // Ligar 
	}
	else {
		lanternDif[0] = 0.0f;
		lanternDif[1] = 0.0f;
		lanternDif[2] = 0.0f;
		lanternDif[3] = 0.0f; // Desligar
	}

	// Componente Specular
	if (specularOn) {
		lanternSpec[0] = 0.10f;
		lanternSpec[1] = 0.10f;
		lanternSpec[2] = 0.10f;
		lanternSpec[3] = 0.35f; // Ligar
	}
	else {
		lanternSpec[0] = 0.0f;
		lanternSpec[1] = 0.0f;
		lanternSpec[2] = 0.0f;
		lanternSpec[3] = 0.0f; // Desligar
	}

	glLightf(GL_LIGHT2, GL_SPOT_CUTOFF, angulo);
	glLightfv(GL_LIGHT2, GL_SPOT_DIRECTION, lanternDir);
	glLightfv(GL_LIGHT2, GL_POSITION, lanternPos);
	glLightfv(GL_LIGHT2, GL_AMBIENT, lanternAmb);
	glLightfv(GL_LIGHT2, GL_DIFFUSE, lanternDif);
	glLightfv(GL_LIGHT2, GL_SPECULAR, lanternSpec);

	if (lanternLight) {
		glEnable(GL_LIGHT2);
	}
	else {
		glDisable(GL_LIGHT2);
	}
}

// Luz Direcional
void ofApp::setupDirectionalLight() {
	glEnable(GL_LIGHTING);
	glEnable(GL_NORMALIZE);

	glEnable(GL_COLOR_MATERIAL);

	glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT);
	glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE);
	glColorMaterial(GL_FRONT_AND_BACK, GL_SPECULAR);
	glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE);

	// Direção
	dirVec[0] = dirVec3f.x;
	dirVec[1] = dirVec3f.y;
	dirVec[2] = dirVec3f.z;
	dirVec[3] = 0;

	// Componente Ambient
	if (ambientOn) {
		dirAmb[0] = 0.1;
		dirAmb[1] = 0.1;
		dirAmb[2] = 0.1;
		dirAmb[3] = 1.0;
	}
	else {
		dirAmb[0] = 0.0;
		dirAmb[1] = 0.0;
		dirAmb[2] = 0.0;
		dirAmb[3] = 0.0;
	}

	// Componente Diffuse
	if (diffuseOn) {
		dirDif[0] = 0.25;
		dirDif[1] = 0.25;
		dirDif[2] = 0.25;
		dirDif[3] = 1.0;
	}
	else {
		dirDif[0] = 0.0;
		dirDif[1] = 0.0;
		dirDif[2] = 0.0;
		dirDif[3] = 0.0;
	}

	// Componente Specular
	if (specularOn) {
		dirSpec[0] = 0.0;
		dirSpec[1] = 0.0;
		dirSpec[2] = 0.0;
		dirSpec[3] = 1.0;
	}
	else {
		dirSpec[0] = 0.0;
		dirSpec[1] = 0.0;
		dirSpec[2] = 0.0;
		dirSpec[3] = 0.0;
	}

	glLightfv(GL_LIGHT0, GL_POSITION, dirVec);
	glLightfv(GL_LIGHT0, GL_AMBIENT, dirAmb);
	glLightfv(GL_LIGHT0, GL_DIFFUSE, dirDif);
	glLightfv(GL_LIGHT0, GL_SPECULAR, dirSpec);

	if (dirOn) {
		glEnable(GL_LIGHT0);
	}
	else {
		glDisable(GL_LIGHT0);
	}
}

//------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

void ofApp::draw() {

	ofBackground(0, 0, 0);

	// Informacao sobre Score e Highscore
	ofDisableLighting();
	
	glPushMatrix();

	glColor3f(1.0, 1.0, 1.0);
	ofDrawBitmapString("Score: " + ofToString(score) + "  HighScore: " + ofToString(highscore), gw() / 2 - 90, gh() / 40);

	glPopMatrix();

	// Informacao sobre Dificuldade
	glPushMatrix();

	glColor3f(1.0, 1.0, 1.0);

	if (hardlevel) {
		ofDrawBitmapString("Dificuldade: Dificil", gw() / 2 - 80, gh() - 10);
	}
	else {
		ofDrawBitmapString("Dificuldade: Facil", gw() / 2 - 80, gh() - 10);
	}
	
	glPopMatrix();

	// Informacao sobre Gameover
	// Apaga tambem todas as luzes
	if (gameover) {
		fruitLight = false;
		lanternLight = false;
		dirOn = false;
		glColor3d(1, 1, 1);
		ofDrawBitmapString("GAME OVER", gw() / 2 - 35, gh() / 2 - 100);

		ofDrawBitmapString("SCORE", gw() / 2 - 20, gh() / 2 - 75);

		ofDrawBitmapString(ofToString(scoreSaved), gw() / 2 - 5, gh() / 2 - 50);

	}

	glColor3f(1.0, 1.0, 1.0);

	ofEnableLighting();

	if (cameraMode == 0) {

		// Viewport maior 
		// Vista em perspetiva
		
		glViewport(0, 0, gw(), gh());
		glMatrixMode(GL_PROJECTION);
		glLoadIdentity();
		perspective(lensAngle, alpha, beta);
		lookat(0, -gh() * 0.65, 0.6 * perfectDist * 1.3f, 0, 0, 0, 0, 1, 0);
		
		drawSnake();
	}

	else if (cameraMode == 1) {
		
		// Viewport maior 
		// Vista ortografica

		glViewport(0, 0, gw(), gh());
		glMatrixMode(GL_PROJECTION);
		glLoadIdentity();
		glOrtho(-gw() * 0.5, gw() * 0.5, -gh() * 0.5, gh() * 0.5, -10000, 10000);
		lookat(0, 0, 1, 0, 0, 0, 0, 1, 0);
		drawSnake();
	}
		
	else if(cameraMode == 2){ 
		
		// Viewport maior
		// Vista em terceira pessoa

		glViewport(0, 0, gw(), gh());

		// Seguir a cabeca da cobra
		ofVec3f head = snakeBody[0];

		// Distancias para camera em terceira pessoa
		float distZ = baseDepth * 15.0f; 
		float distY = baseHeight * 10.0f; 

		// Posiçao da camera     
		float cameraPositionX = -floorWidth * 0.5 + (head.x * baseWidth) + baseWidth * 0.5;
		float cameraPositionY = floorHeight * 0.5 - (head.y * baseHeight) - baseHeight * 0.5 - distY;
		float cameraPositionZ = basePosZ + distZ;

		// Foco na cabeça da cobra
		float targetPositionX = -floorWidth * 0.5 + (head.x * baseWidth) + baseWidth * 0.5;
		float targetPositionY = floorHeight * 0.5 - (head.y * baseHeight) - baseHeight * 0.5;
		float targetPositionZ = basePosZ;

		glMatrixMode(GL_PROJECTION);
		glLoadIdentity();
		perspective(lensAngle, alpha, beta);

		lookat(cameraPositionX, cameraPositionY, cameraPositionZ,
			targetPositionX, targetPositionY, targetPositionZ,
			0, 0, 1);

		drawSnake();
	}
	glColor3f(1.0, 1.0, 1.0);

	setupDirectionalLight();
	
	// Sol
	if (dirOn) {

		// Textura para o Sol
		sunTexture.bind();

		glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL); // GL_MODULATE PARA RETIRAR BRILHO NATURAL
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);

		glPushMatrix();

		glTranslatef(cubePosX, 0.0f, cubePosZ);
		glScalef(baseWidth, baseHeight, baseDepth);
		cube_unit(298);

		glPopMatrix();

		sunTexture.unbind();
	}

	// Colocar Lanterna na Cabeca da Cobra
	setupLanternLight();
}

//--------------------------------------------------------------

bool ofApp::checkCollisionWithFruit() {
	if (basePosX == fruitPosX && basePosY == fruitPosY) {
		return 1;
	}

	return 0;
}

//--------------------------------------------------------------

bool ofApp::checkSelfCollision() {
	ofVec3f head = snakeBody[0];
	
	if (snakeBody.size() > 2) {
		for (int i = 1; i < snakeBody.size(); i++) {

			if (snakeBody[i].x == head.x && snakeBody[i].y == head.y) {
				return 1;
			}
		}
	}
	return 0;
}

//--------------------------------------------------------------

void ofApp::generateFruitPosition() {
	bool check; 
	fruitScale = 0.0f;
	fruitProgress = 0.0f;
	do {
		check = 0;
		fruitPosX = rand() % resX;  // Posição aleatória X
		fruitPosY = rand() % resY;  // Posição aleatória y

		for (int i = 0; i < snakeBody.size(); i++) {
			if (fruitPosX == snakeBody[i].x && fruitPosY == snakeBody[i].y) { // Verificaçao para nao gerar fruta dentro da cobra
				check = 1;
				break;
			}
		}

	} while (check);	
}

//--------------------------------------------------------------

void ofApp::addSnakeUnit() {
	ofVec3f lastSegment = snakeBody.back();
	snakeBody.push_back(lastSegment);         
}

//--------------------------------------------------------------

void ofApp::setupSnake() {

	// Campo de jogo
	resX = 25 ;
	resY = 25;
	floorWidth = gw() * 0.5;
	floorHeight = gw() * 0.5;
	floorHeightPos = 0.;

	// Medidas de cada unidade da snake
	baseWidth = floorWidth / GLfloat(resX);
	baseHeight = floorHeight / GLfloat(resY);
	baseDepth = baseWidth ;

	basePosX = floor(resX / 2.0f);
	basePosY = floor(resY / 2.0f);
	basePosZ = floorHeightPos + baseDepth * 0.5;
}

//--------------------------------------------------------------

void ofApp::drawSnake() {

	// Desenhar o campo

	// Textura do campo
	fieldTexture.bind();

	glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);

	// Alterar cores da textura
	glColor3f(0.5, 1.0, 0.0);

	glPushMatrix();

	glScalef(floorWidth, floorHeight, 1.0);
	malha_unit(resX, resY);

	glPopMatrix();
	
	snakeTexture.unbind();

	// Textura para a cobra
	snakeTexture.bind();
	glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL);  // GL_MODULATE PARA RETIRAR BRILHO NATURAL
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);

	// Desenhar os cubos da cobra nas posições corretas
	for (ofVec3f& segment : snakeBody) {
		glPushMatrix();

		glTranslatef(-floorWidth * 0.5 + (segment.x * baseWidth) + baseWidth * 0.5,
			floorHeight * 0.5 - (segment.y * baseHeight) - baseHeight * 0.5,
			segment.z);

		glScalef(baseWidth * modifyScale, baseHeight * modifyScale, baseDepth * modifyScale);


		cube_unit(100);
		
	}

	snakeTexture.unbind();

	// Textura para a Fruta
	appleTexture.bind();
	glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL); // GL_MODULATE PARA RETIRAR BRILHO NATURAL
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);

	// Desenha a Fruta
	glPushMatrix();

	glTranslatef(-floorWidth * 0.5 + (fruitPosX * baseWidth) + baseWidth * 0.5,
		floorHeight * 0.5 - (fruitPosY * baseHeight) - baseHeight * 0.5,
		basePosZ);

	glScalef(baseWidth * fruitScale, baseHeight * fruitScale, baseDepth * fruitScale);
	cube_unit(210);

	glPopMatrix();

	setupFruitLight();

	appleTexture.unbind();
}



//--------------------------------------------------------------

void ofApp::explodingEffect(GLfloat time) {

	explosionTime += time;

	for (int i = 0; i < snakeBody.size(); ++i) {
		ofVec3f direction(ofRandom(-1, 1), ofRandom(-1, 1), 0);
		snakeBody[i] += direction * time * 7.5f; // Multiplicado por time para que seja consistente com o tempo

		float scale = 1.0f - (explosionTime / 1.0f);  // Escala decresce até 0
		if (scale < 0.0f) scale = 0.0f;  // Evitar escala negativa
		modifyScale = scale;
	}

	if (explosionTime > 1.0f) {

		// Repor variaveis
		exploding = false;

		basePosX = floor(resX / 2.0f);
		basePosY = floor(resY / 2.0f);

		directionX = 0.0;
		directionY = 0.0;

		snakeSpeed = 0.15f;
		modifyScale = 1.00f;
		snakeBody.clear();
		snakeBody.push_back(ofVec3f(basePosX, basePosY, basePosZ));

		generateFruitPosition();
	}
}

//--------------------------------------------------------------

void ofApp::eatEffect(GLfloat time){
	eatingDuration = 2.0f;
	temporizador += time;

	float progress = temporizador / eatingDuration;

	if (progress <= 0.5f) {
		float pulse = sin(progress * PI * 6);
		modifyScale = 1.0f + 0.25f * (0.5f * (pulse + 1));
	}

	else {
		// Repor variaveis
		eating = false;
		modifyScale = 1.0f;
		temporizador = 0.0f;
	}
}

//--------------------------------------------------------------

void ofApp::wallCollisonEffect(GLfloat time) {
	collidingTime += time;
	
	if (collidingTime >= collidingInterval) {
		collidingTime = 0.0f;
		snakeBody.pop_back();
		if (snakeBody.empty()) {

			//Repor variaveis
			colliding = false;
			basePosX = floor(resX / 2.0f);
			basePosY = floor(resY / 2.0f);

			directionX = 0.0;
			directionY = 0.0;

			snakeSpeed = 0.15f; 

			snakeBody.clear();
			snakeBody.push_back(ofVec3f(basePosX, basePosY, basePosZ)); 

			generateFruitPosition();
		}
	}
}

//--------------------------------------------------------------

void ofApp::keyPressed(int key) {

	// Gameover passa a false se clicar em alguma tecla
	gameover = false;

	if (verifica) {
		switch (key) {
			case OF_KEY_LEFT :
				if (directionX != 1.0 || snakeBody.size() < 2) {
					directionX = -1.0;
					directionY = 0.0;
					verifica = 0;
					
				}
				break;
			case OF_KEY_RIGHT  :
				if (directionX != -1.0 || snakeBody.size() < 2) {
					directionX = 1.0;
					directionY = 0.0;
					verifica = 0;
				}
				break;
			case OF_KEY_UP:
				if (directionY != 1.0 || snakeBody.size() < 2) {
					directionX = 0.0;
					directionY = -1.0;
					verifica = 0;
				}
				break;
			case OF_KEY_DOWN:
				if (directionY != -1.0 || snakeBody.size() < 2) {
					directionX = 0.0;
					directionY = 1.0;
					verifica = 0;
				}
				break;
			case 'v':
				cameraMode = (cameraMode + 1) % 3;
				break;
			case 'b': 
				fruitLight = !fruitLight;
				break;
			case 'l':
				lanternLight = !lanternLight; 
				break;
			case 'm':
				// So permite alterar a dificuldade quando o jogo esta parado
				if (directionX == 0 && directionY == 0) {
					hardlevel = !hardlevel;
				}
				break;
			case 's':
				dirOn = !dirOn;
				sunMoving = false;
				break;
			case 'd':
				sunMoving = !sunMoving;
				break;
			case '1':
				ambientOn = !ambientOn;
				break;
			case '2':
				diffuseOn = !diffuseOn;
				break;
			case '3':
				specularOn = !specularOn;
				break;
		}
	}
}

//--------------------------------------------------------------
void ofApp::keyReleased(int key) {

}

//--------------------------------------------------------------
void ofApp::mouseMoved(int x, int y) {

}

//--------------------------------------------------------------
void ofApp::mouseDragged(int x, int y, int button) {

}

//--------------------------------------------------------------
void ofApp::mousePressed(int x, int y, int button) {

}

//--------------------------------------------------------------
void ofApp::mouseReleased(int x, int y, int button) {

}

//--------------------------------------------------------------
void ofApp::mouseEntered(int x, int y) {

}

//--------------------------------------------------------------
void ofApp::mouseExited(int x, int y) {

}

//--------------------------------------------------------------
void ofApp::windowResized(int w, int h) {
	GLint save = highscore;
	setup();
	highscore = save;
}

//--------------------------------------------------------------
void ofApp::gotMessage(ofMessage msg) {

}

//--------------------------------------------------------------
void ofApp::dragEvent(ofDragInfo dragInfo) {

}
