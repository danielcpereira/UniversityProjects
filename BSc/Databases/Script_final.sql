CREATE TABLE pessoa (
	numero_cc	 INTEGER,
	nome		 VARCHAR(512) NOT NULL,
	data_nascimento DATE NOT NULL,
	mail		 VARCHAR(512) NOT NULL,
	password	 VARCHAR(512) NOT NULL,
	PRIMARY KEY(numero_cc)
);

CREATE TABLE paciente (
	pessoa_numero_cc INTEGER,
	PRIMARY KEY(pessoa_numero_cc)
);

CREATE TABLE funcionario (
	id_funcionario	 SERIAL NOT NULL,
	contrato_valido	 BOOL NOT NULL,
	inicio_contrato_atual DATE NOT NULL,
	salario		 NUMERIC(8,2) NOT NULL,
	pessoa_numero_cc	 INTEGER,
	PRIMARY KEY(pessoa_numero_cc)
);

CREATE TABLE medico (
	licenca_medica		 INTEGER NOT NULL,
	funcionario_pessoa_numero_cc INTEGER,
	PRIMARY KEY(funcionario_pessoa_numero_cc)
);

CREATE TABLE enfermeiro (
	cat_herarquica		 VARCHAR(512) NOT NULL,
	funcionario_pessoa_numero_cc INTEGER,
	PRIMARY KEY(funcionario_pessoa_numero_cc)
);

CREATE TABLE assistente (
	funcionario_pessoa_numero_cc INTEGER,
	PRIMARY KEY(funcionario_pessoa_numero_cc)
);

CREATE TABLE consulta (
	id_consulta			 INTEGER,
	data_consulta			 TIMESTAMP NOT NULL,
	preco				 INTEGER NOT NULL DEFAULT 20,
	especialidade_id_especialidade	 INTEGER NOT NULL,
	fatura_id_despesa			 INTEGER NOT NULL,
	medico_funcionario_pessoa_numero_cc INTEGER NOT NULL,
	paciente_pessoa_numero_cc		 INTEGER NOT NULL,
	PRIMARY KEY(id_consulta)
);

CREATE TABLE internamento (
	id_internamento			 SERIAL,
	inicio					 TIMESTAMP NOT NULL,
	terminado				 BOOL NOT NULL,
	preco					 INTEGER NOT NULL DEFAULT 50,
	fatura_id_despesa			 INTEGER NOT NULL,
	paciente_pessoa_numero_cc		 INTEGER NOT NULL,
	assistente_funcionario_pessoa_numero_cc INTEGER NOT NULL,
	enfermeiro_funcionario_pessoa_numero_cc INTEGER NOT NULL,
	PRIMARY KEY(id_internamento)
);

CREATE TABLE cirurgia (
	id_cirurgia			 BIGSERIAL,
	tipo				 VARCHAR(512),
	data_cirurgia			 TIMESTAMP NOT NULL,
	preco				 INTEGER NOT NULL DEFAULT 80,
	paciente_pessoa_numero_cc		 INTEGER NOT NULL,
	especialidade_id_especialidade	 INTEGER NOT NULL,
	fatura_id_despesa			 INTEGER NOT NULL,
	medico_funcionario_pessoa_numero_cc INTEGER NOT NULL,
	internamento_id_internamento	 INTEGER NOT NULL,
	PRIMARY KEY(id_cirurgia)
);

CREATE TABLE receita (
	id_receita SERIAL,
	validade	 DATE,
	PRIMARY KEY(id_receita)
);

CREATE TABLE especialidade (
	id_especialidade SERIAL,
	nome		 VARCHAR(512) NOT NULL,
	parent		 TEXT NOT NULL,
	PRIMARY KEY(id_especialidade)
);

CREATE TABLE fatura (
	id_despesa		 SERIAL,
	montante			 NUMERIC(8,2) NOT NULL,
	liquidacao		 BOOL NOT NULL,
	paciente_pessoa_numero_cc INTEGER NOT NULL,
	PRIMARY KEY(id_despesa)
);

CREATE TABLE pagamento (
	id_pagamento	 BIGSERIAL,
	metodo		 VARCHAR(512) NOT NULL,
	montante		 INTEGER NOT NULL,
	data		 DATE NOT NULL,
	fatura_id_despesa INTEGER NOT NULL,
	PRIMARY KEY(id_pagamento)
);

CREATE TABLE medicamento (
	id_medicamento	 SERIAL,
	nome		 VARCHAR(512) NOT NULL,
	dosagem		 NUMERIC(8,2) NOT NULL,
	frequencia	 INTEGER NOT NULL,
	receita_id_receita INTEGER NOT NULL,
	PRIMARY KEY(id_medicamento)
);

CREATE TABLE efeito_colateral (
	nome			 TEXT NOT NULL,
	gravidade			 NUMERIC(8,2) NOT NULL,
	probabilidade		 INTEGER NOT NULL,
	medicamento_id_medicamento INTEGER NOT NULL
);

CREATE TABLE medico_especialidade (
	medico_funcionario_pessoa_numero_cc INTEGER,
	especialidade_id_especialidade	 INTEGER,
	PRIMARY KEY(medico_funcionario_pessoa_numero_cc,especialidade_id_especialidade)
);

CREATE TABLE consulta_receita (
	consulta_id_consulta INTEGER NOT NULL,
	receita_id_receita	 INTEGER,
	PRIMARY KEY(receita_id_receita)
);

CREATE TABLE receita_internamento (
	receita_id_receita		 INTEGER,
	internamento_id_internamento INTEGER NOT NULL,
	PRIMARY KEY(receita_id_receita)
);

CREATE TABLE enfermeiro_cirurgia (
	enfermeiro_funcionario_pessoa_numero_cc INTEGER,
	cirurgia_id_cirurgia			 BIGINT,
	PRIMARY KEY(enfermeiro_funcionario_pessoa_numero_cc,cirurgia_id_cirurgia)
);

ALTER TABLE pessoa ADD UNIQUE (mail);
ALTER TABLE paciente ADD CONSTRAINT paciente_fk1 FOREIGN KEY (pessoa_numero_cc) REFERENCES pessoa(numero_cc);
ALTER TABLE funcionario ADD UNIQUE (id_funcionario);
ALTER TABLE funcionario ADD CONSTRAINT funcionario_fk1 FOREIGN KEY (pessoa_numero_cc) REFERENCES pessoa(numero_cc);
ALTER TABLE medico ADD UNIQUE (licenca_medica);
ALTER TABLE medico ADD CONSTRAINT medico_fk1 FOREIGN KEY (funcionario_pessoa_numero_cc) REFERENCES funcionario(pessoa_numero_cc);
ALTER TABLE enfermeiro ADD CONSTRAINT enfermeiro_fk1 FOREIGN KEY (funcionario_pessoa_numero_cc) REFERENCES funcionario(pessoa_numero_cc);
ALTER TABLE assistente ADD CONSTRAINT assistente_fk1 FOREIGN KEY (funcionario_pessoa_numero_cc) REFERENCES funcionario(pessoa_numero_cc);
ALTER TABLE consulta ADD CONSTRAINT consulta_fk1 FOREIGN KEY (especialidade_id_especialidade) REFERENCES especialidade(id_especialidade);
ALTER TABLE consulta ADD CONSTRAINT consulta_fk2 FOREIGN KEY (fatura_id_despesa) REFERENCES fatura(id_despesa);
ALTER TABLE consulta ADD CONSTRAINT consulta_fk3 FOREIGN KEY (medico_funcionario_pessoa_numero_cc) REFERENCES medico(funcionario_pessoa_numero_cc);
ALTER TABLE consulta ADD CONSTRAINT consulta_fk4 FOREIGN KEY (paciente_pessoa_numero_cc) REFERENCES paciente(pessoa_numero_cc);
ALTER TABLE internamento ADD CONSTRAINT internamento_fk1 FOREIGN KEY (fatura_id_despesa) REFERENCES fatura(id_despesa);
ALTER TABLE internamento ADD CONSTRAINT internamento_fk2 FOREIGN KEY (paciente_pessoa_numero_cc) REFERENCES paciente(pessoa_numero_cc);
ALTER TABLE internamento ADD CONSTRAINT internamento_fk3 FOREIGN KEY (assistente_funcionario_pessoa_numero_cc) REFERENCES assistente(funcionario_pessoa_numero_cc);
ALTER TABLE internamento ADD CONSTRAINT internamento_fk4 FOREIGN KEY (enfermeiro_funcionario_pessoa_numero_cc) REFERENCES enfermeiro(funcionario_pessoa_numero_cc);
ALTER TABLE cirurgia ADD CONSTRAINT cirurgia_fk1 FOREIGN KEY (paciente_pessoa_numero_cc) REFERENCES paciente(pessoa_numero_cc);
ALTER TABLE cirurgia ADD CONSTRAINT cirurgia_fk2 FOREIGN KEY (especialidade_id_especialidade) REFERENCES especialidade(id_especialidade);
ALTER TABLE cirurgia ADD CONSTRAINT cirurgia_fk3 FOREIGN KEY (fatura_id_despesa) REFERENCES fatura(id_despesa);
ALTER TABLE cirurgia ADD CONSTRAINT cirurgia_fk4 FOREIGN KEY (medico_funcionario_pessoa_numero_cc) REFERENCES medico(funcionario_pessoa_numero_cc);
ALTER TABLE cirurgia ADD CONSTRAINT cirurgia_fk5 FOREIGN KEY (internamento_id_internamento) REFERENCES internamento(id_internamento);
ALTER TABLE especialidade ADD UNIQUE (nome);
ALTER TABLE fatura ADD CONSTRAINT fatura_fk1 FOREIGN KEY (paciente_pessoa_numero_cc) REFERENCES paciente(pessoa_numero_cc);
ALTER TABLE pagamento ADD CONSTRAINT pagamento_fk1 FOREIGN KEY (fatura_id_despesa) REFERENCES fatura(id_despesa);
ALTER TABLE medicamento ADD CONSTRAINT medicamento_fk1 FOREIGN KEY (receita_id_receita) REFERENCES receita(id_receita);
ALTER TABLE efeito_colateral ADD CONSTRAINT efeito_colateral_fk1 FOREIGN KEY (medicamento_id_medicamento) REFERENCES medicamento(id_medicamento);
ALTER TABLE medico_especialidade ADD CONSTRAINT medico_especialidade_fk1 FOREIGN KEY (medico_funcionario_pessoa_numero_cc) REFERENCES medico(funcionario_pessoa_numero_cc);
ALTER TABLE medico_especialidade ADD CONSTRAINT medico_especialidade_fk2 FOREIGN KEY (especialidade_id_especialidade) REFERENCES especialidade(id_especialidade);
ALTER TABLE consulta_receita ADD CONSTRAINT consulta_receita_fk1 FOREIGN KEY (consulta_id_consulta) REFERENCES consulta(id_consulta);
ALTER TABLE consulta_receita ADD CONSTRAINT consulta_receita_fk2 FOREIGN KEY (receita_id_receita) REFERENCES receita(id_receita);
ALTER TABLE receita_internamento ADD CONSTRAINT receita_internamento_fk1 FOREIGN KEY (receita_id_receita) REFERENCES receita(id_receita);
ALTER TABLE receita_internamento ADD CONSTRAINT receita_internamento_fk2 FOREIGN KEY (internamento_id_internamento) REFERENCES internamento(id_internamento);
ALTER TABLE enfermeiro_cirurgia ADD CONSTRAINT enfermeiro_cirurgia_fk1 FOREIGN KEY (enfermeiro_funcionario_pessoa_numero_cc) REFERENCES enfermeiro(funcionario_pessoa_numero_cc);
ALTER TABLE enfermeiro_cirurgia ADD CONSTRAINT enfermeiro_cirurgia_fk2 FOREIGN KEY (cirurgia_id_cirurgia) REFERENCES cirurgia(id_cirurgia);

