/*CG_EXTRAS
collection of functions to help speed up programming in OF

Developed for the Computer Graphics course @:
Informatics Engineering Department
University of Coimbra
by
André Perrotta & Evgheni Polisciuc

Coimbra, 09/2023
*/

#ifndef CG_EXTRAS_H
#define CG_EXTRAS_H

#include "ofMain.h"

//short named function to get screen width
inline float gw() {
	return ofGetWidth();
}

//short named function to get screen height
inline float gh() {
	return ofGetHeight();
}

//short named function to put Frame Rate as window title
inline void setFrWt() {
	ofSetWindowTitle(ofToString(ofGetFrameRate()));
}


inline ofVec3f cross(ofVec3f A, ofVec3f B) {
	ofVec3f aux;
	aux.x = A.y * B.z - A.z * B.y;
	aux.y = A.z * B.x - A.x * B.z;
	aux.z = A.x * B.y - A.y * B.x;

	return aux;
}

#endif