import gymnasium as gym
import numpy as np
import pygame

ENABLE_WIND = 1
WIND_POWER = 15.0
TURBULENCE_POWER = 0.0
GRAVITY = -10.0
RENDER_MODE = 'human'
RENDER_MODE = None
EPISODES = 1000

env = gym.make("LunarLander-v3", render_mode =RENDER_MODE, 
    continuous=True, gravity=GRAVITY, 
    enable_wind=ENABLE_WIND, wind_power=WIND_POWER, 
    turbulence_power=TURBULENCE_POWER)

def check_successful_landing(observation):
    x = observation[0]
    vy = observation[3]
    theta = observation[4]
    contact_left = observation[6]
    contact_right = observation[7]

    legs_touching = contact_left == 1 and contact_right == 1

    on_landing_pad = abs(x) <= 0.2

    stable_velocity = vy > -0.2
    stable_orientation = abs(theta) < np.deg2rad(20)
    stable = stable_velocity and stable_orientation
 
    if legs_touching and on_landing_pad and stable:
        print("✅ Aterragem bem sucedida!")
        return True

    print("⚠️ Aterragem falhada!")        
    return False

def simulate(steps=1000,seed=None, policy = None):    
    observ, _ = env.reset(seed=seed)
    for step in range(steps):
        action = policy(observ)
        observ, _, term, trunc, _ = env.step(action)

        if term or trunc:
            break

    success = check_successful_landing(observ)
    return step, success


#Perceptions

##Coordenadas
def px(observation):
    return observation[0]

def py(observation):
    return observation[1]

##Componentes da Velocidade
def vx(observation):
    return observation[2]

def vy(observation):
    return observation[3]

##Orientações
def theta(observation):
    return observation[4]

def vtheta(observation):
    return observation[5]

##Booleanos de contacto com o solo 
def pe(observation):
    return observation[6]

def pd(observation):
    return observation[7]


#Actions

##Ativar Motor Principal
def main_engine():
    return [1.0, 0.0]
   
##Ativar Motor Secundario Esquerdo            
def left_engine():
    return [0.0, -1.0]

##Ativar Motor Secundario Direito   
def right_engine():
    return [0.0, 1.0]

#Agente sem vento
def reactive_agent(observation):
    action = [0.0, 0.0]

    #Correção da velocidade horizontal
    if vx(observation) > 0.1:
        action = np.add(action, left_engine())  
    elif vx(observation) < -0.1:
        action = np.add(action, right_engine())

    #Correção da velocidade vertical
    if vy(observation) < -0.3:  
        action = np.add(action, main_engine())
    if vy(observation) < -0.1 and py(observation) < 0.3:  
        action = np.add(action, main_engine())   
    
    #Correção da orientação e da velocidade angular
    if theta(observation) > np.deg2rad(3):  
        action = np.add(action, right_engine())    
    elif theta(observation) < -np.deg2rad(3):  
        action = np.add(action, left_engine())
    
    if  vtheta(observation) > 0.2:  
        action = np.add(action, right_engine())  
    elif  vtheta(observation) < -0.2:
        action = np.add(action, left_engine()) 

    #Correção da posição horizontal
    if px(observation) < -0.2: 
        action = np.add(action, right_engine())  
    elif px(observation) > 0.2:
        action = np.add(action, left_engine())

    return action
    
def reactive_agent_wind(observation):
    action = [0.0, 0.0]

    #Correção da velocidade horizontal
    if vx(observation) > 0.05:
        action = np.add(action, left_engine())  
    elif vx(observation) < -0.05:
        action = np.add(action, right_engine())

    #Correção da velocidade vertical
    if vy(observation) < -0.3:  
        action = np.add(action, main_engine())
    if vy(observation) < -0.3 and py(observation) < 0.3:  
        action = np.add(action, main_engine())   
    
    #Correção da orientação e da velocidade angular
    if theta(observation) > np.deg2rad(5):  
        action = np.add(action, right_engine())    
    elif theta(observation) < -np.deg2rad(5):  
        action = np.add(action, left_engine())
    
    if  vtheta(observation) > 0.2:  
        action = np.add(action, right_engine())  
    elif  vtheta(observation) < -0.2:
        action = np.add(action, left_engine()) 

    #Correção da posição horizontal
    if px(observation) < -0.2: 
        action = np.add(action, right_engine())  
    elif px(observation) > 0.2:
        action = np.add(action, left_engine())

    return action

def keyboard_agent(observation):
    action = [0,0] 
    keys = pygame.key.get_pressed()
    
    print('observação:',observation)

    if keys[pygame.K_UP]:  
        action =+ np.array([1,0])
    if keys[pygame.K_LEFT]:  
        action =+ np.array( [0,-1])
    if keys[pygame.K_RIGHT]: 
        action =+ np.array([0,1])

    return action
    

success = 0.0
steps = 0.0
for i in range(EPISODES):
    #Se o vento estiver desativado
    if ENABLE_WIND == 0:
        st, su = simulate(steps=1000000, policy=reactive_agent)
    #Se o vento estiver ativado
    else:
        st, su = simulate(steps=1000000, policy=reactive_agent_wind)
    
    if su:
        steps += st
    success += su
    
    if su>0:
        print('Média de passos das aterragens bem sucedidas:', steps/success*100)
    print('Taxa de sucesso:', success/(i+1)*100)