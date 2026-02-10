#pragma once

#include "ofMain.h"
#include "cg_extras.h"

// Desenha ponto 3D na origem
inline void drawPoint() {
	glBegin(GL_POINTS);
	glVertex3f(0, 0, 0);
	glEnd();
}

// Desenha axis 3D
inline void axis3d() {
	glBegin(GL_LINES);
	glColor3f(1, 0, 0);
	glVertex3f(0, 0, 0);
	glVertex3f(1, 0, 0);
	glColor3f(0, 1, 0);
	glVertex3f(0, 0, 0);
	glVertex3f(0, 1, 0);
	glColor3f(1, 1, 1);
	glVertex3f(0, 0, 0);
	glVertex3f(0, 0, 1);
	glEnd();
}

inline void malha_unit(GLint m, GLint n) {
	GLfloat x_start = -0.5;
	GLfloat y_start = 0.5;
	GLfloat x_step = 1.0 / GLfloat(m);
	GLfloat y_step = 1.0 / GLfloat(n);

	GLfloat imageX = 1827.0 / GLfloat(m); 

	GLfloat imageY = 1827.0 / GLfloat(n); 

	glBegin(GL_QUADS);
	glNormal3f(0, 0, 1);

	for (int i = 0; i < m; i++) {
		for (int j = 0; j < n; j++) {
			
			GLfloat x_min = i * imageX;
			GLfloat x_max = (i + 1) * imageX;

			GLfloat y_min = j * imageY;
			GLfloat y_max = (j + 1) * imageY;

			glTexCoord2f(x_min, y_min); glVertex2d(i * x_step + x_start, y_start - j * y_step);
			glTexCoord2f(x_min, y_max); glVertex2d(i * x_step + x_start, y_start - (j + 1) * y_step);
			glTexCoord2f(x_max, y_max); glVertex2d((i + 1) * x_step + x_start, y_start - (j + 1) * y_step);
			glTexCoord2f(x_max, y_min); glVertex2d((i + 1) * x_step + x_start, y_start - j * y_step);
		}
	}
	glEnd();
}



inline void cube_unit(GLint ti) {
	glBegin(GL_QUADS);
	
	// Front Face
	glTexCoord2f(0, 0); glVertex3f(-0.5, -0.5, 0.5);
	glTexCoord2f(ti, 0); glVertex3f(0.5, -0.5, 0.5);
	glTexCoord2f(ti, ti); glVertex3f(0.5, 0.5, 0.5);
	glTexCoord2f(0, ti); glVertex3f(-0.5, 0.5, 0.5);

	// Back Face
	glTexCoord2f(0, 0); glVertex3f(-0.5, -0.5, -0.5);
	glTexCoord2f(ti, 0); glVertex3f(0.5, -0.5, -0.5);
	glTexCoord2f(ti, ti); glVertex3f(0.5, 0.5, -0.5);
	glTexCoord2f(0, ti); glVertex3f(-0.5, 0.5, -0.5);

	// Left Face
	glTexCoord2f(0, 0); glVertex3f(-0.5, -0.5, -0.5);
	glTexCoord2f(ti, 0); glVertex3f(-0.5, -0.5, 0.5);
	glTexCoord2f(ti, ti); glVertex3f(-0.5, 0.5, 0.5);
	glTexCoord2f(0, ti); glVertex3f(-0.5, 0.5, -0.5);

	// Right Face
	glTexCoord2f(0, 0); glVertex3f(0.5, -0.5, -0.5);
	glTexCoord2f(ti, 0); glVertex3f(0.5, -0.5, 0.5);
	glTexCoord2f(ti, ti); glVertex3f(0.5, 0.5, 0.5);
	glTexCoord2f(0, ti); glVertex3f(0.5, 0.5, -0.5);

	// Top Face
	glTexCoord2f(0, 0); glVertex3f(-0.5, 0.5, -0.5);
	glTexCoord2f(ti, 0); glVertex3f(0.5, 0.5, -0.5);
	glTexCoord2f(ti, ti); glVertex3f(0.5, 0.5, 0.5);
	glTexCoord2f(0, ti); glVertex3f(-0.5, 0.5, 0.5);

	// Bottom Face
	glTexCoord2f(0, 0); glVertex3f(-0.5, -0.5, -0.5);
	glTexCoord2f(ti, 0); glVertex3f(0.5, -0.5, -0.5);
	glTexCoord2f(ti, ti); glVertex3f(0.5, -0.5, 0.5);
	glTexCoord2f(0, ti); glVertex3f(-0.5, -0.5, 0.5);
	glEnd();

	glPopMatrix();

	glEnd();

}

