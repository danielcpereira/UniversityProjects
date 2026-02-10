/*
Daniel Pereira Nº 2021237092
Manuel Couto   Nº 2021233121
*/
%{
    #include <stdlib.h>
    #include <stdio.h>
    #include <string.h>
    #include "y.tab.h"
    #include "tree.h"
    #include "symbol_table.h"

    extern int yylex();
    void yyerror(char* s);
    int yylex_destroy(void);

    char* type;

    extern int flagl;
    int flagt=0; 
    
    struct node *program;
    struct node *aux;

    int eof = 0;
    int errorY =0 ;

    int flags = 0;


%}

%token<lexeme> PACKAGE IDENTIFIER SEMICOLON
%token<lexeme> NATURAL DECIMAL VAR LPAR RPAR COMMA
%token<lexeme> INT FLOAT32 BOOL STRING1
%token<lexeme> FUNC LBRACE RBRACE 

%token<lexeme> ASSIGN OR AND LT GT EQ NE LE GE
%token<lexeme> PLUS MINUS STAR DIV MOD
%token<lexeme> NOT PRINT STRLIT RETURN FOR IF ELSE
%token<lexeme> BLANKID PARSEINT CMDARGS LSQ RSQ  

%left COMMA
%right ASSIGN 
%left OR
%left AND
%left EQ NE LT GT LE GE
%left PLUS MINUS
%left STAR DIV MOD
%right NOT



%type <node> Program 
%type <node> Declarations VarDeclaration VarSpec_2 Type
%type <node> FuncDeclaration FuncBody
%type <node> Parameters Parameters_2 ParamDecl
%type <node> VarsAndStatements Statement Statement_2
%type <node> Expr ParseArgs FuncInvocation FuncInvocation_2   


%union{
    char *lexeme;
    struct node *node;
}

%%

Program:
    PACKAGE IDENTIFIER SEMICOLON Declarations           { $$ = program = new_node("Program", NULL); add_childs(program, 1, $4);}    
    ; 

Declarations:   
     VarDeclaration SEMICOLON Declarations              { $$ = $1; if($3) add_sibling($$, $3);}
    |FuncDeclaration SEMICOLON Declarations             { $$ = $1; if($3) add_sibling($$, $3);}
    |                                                   { $$ = NULL;}
    ;

VarDeclaration:
     VAR IDENTIFIER VarSpec_2 Type                      { $$ = new_node("VarDecl", NULL);  
                                                        add_childs($$, 2, $4, new_node("Identifier", $2));  
                                                        
                                                        if($3){ update_type($3,$4); add_sibling($$, $3); }}


    |VAR LPAR IDENTIFIER VarSpec_2 Type SEMICOLON RPAR  { $$ = new_node("VarDecl", NULL);  
                                                        add_childs($$, 2, $5, new_node("Identifier", $3));  
                                                       
                                                        if($4){ update_type($4,$5);  add_sibling($$, $4); }}
    ;
  
VarSpec_2:
    COMMA IDENTIFIER VarSpec_2                          {$$ = new_node("VarDecl", NULL);
                                                        add_childs($$, 1, new_node("Identifier", $2) );
                                                        if($3){add_sibling($$, $3);}}
                                                        
    |                                                   { $$ = NULL;}
    ;
 
Type:
    INT                                                 {$$ = new_node("Int", NULL);}
    | FLOAT32                                           {$$ = new_node("Float32", NULL);}
    | BOOL                                              {$$ = new_node("Bool", NULL);}
    | STRING1                                           {$$ = new_node("String", NULL);}
    ;

FuncDeclaration:
    FUNC IDENTIFIER LPAR Parameters RPAR Type FuncBody {$$ = new_node("FuncDecl",NULL);
                                                        node *aux = new_node("FuncHeader",NULL);
                                                        add_childs(aux, 3, new_node("Identifier",$2),$6,$4);
                                                        add_childs($$, 2, aux, $7);}

    |FUNC IDENTIFIER LPAR RPAR Type FuncBody           {$$ = new_node("FuncDecl",NULL);
                                                        node *aux = new_node("FuncHeader",NULL);
                                                        add_childs(aux, 3, new_node("Identifier",$2), $5, new_node("FuncParams",NULL));
                                                        add_childs($$, 2, aux, $6);}
                                                            
    |FUNC IDENTIFIER LPAR RPAR FuncBody                {$$ = new_node("FuncDecl",NULL);
                                                        node *aux = new_node("FuncHeader",NULL);
                                                        add_childs(aux, 2, new_node("Identifier",$2),  new_node("FuncParams",NULL));
                                                        add_childs($$, 2, aux, $5);}

    |FUNC IDENTIFIER LPAR Parameters RPAR FuncBody     { $$ = new_node("FuncDecl",NULL);
                                                        node *aux = new_node("FuncHeader",NULL);
                                                        add_childs(aux, 2, new_node("Identifier",$2), $4);
                                                        add_childs($$, 2, aux, $6);}
    ;

Parameters:
    ParamDecl Parameters_2                             {$$  = new_node("FuncParams", NULL); add_childs($$, 2, $1, $2);}
    ;

Parameters_2:
    COMMA ParamDecl Parameters_2                      { $$=$2;if($3)add_sibling($$,$3);} 
    |                                                 { $$ = NULL;}
    ; 
ParamDecl:
    IDENTIFIER Type                                   {$$ = new_node("ParamDecl",NULL);add_childs($$, 2, $2, new_node("Identifier",$1));}                     
    ;

FuncBody:
    LBRACE VarsAndStatements RBRACE                   { $$ = new_node("FuncBody", NULL); add_childs($$,1,$2);}
    ;
VarsAndStatements:
     VarDeclaration SEMICOLON VarsAndStatements       { if($$){ $$ = $1; if($3)add_sibling($$,$3); } else {$$ = $3;}}
    |Statement SEMICOLON VarsAndStatements            { if($$){ $$ = $1; if($3)add_sibling($$,$3); } else {$$ = $3;}}
    |SEMICOLON VarsAndStatements                      { $$ = $2;}
    |                                                 { $$ = NULL;}
    ;

Statement:
      IDENTIFIER ASSIGN Expr                                                {$$ = new_node("Assign", NULL);
                                                                            add_childs($$, 2, new_node("Identifier", $1), $3);}

     |LBRACE Statement_2 RBRACE                                             {if($2){
                                                                                if(calculate_depth($2)>=2){
                                                                                    $$ = new_node("Block", NULL); add_childs($$, 1, $2);
                                                                                }  else {$$ = $2;} 
                                                                             }  
                                                                             else{$$ = NULL; }} 

     |IF Expr LBRACE Statement_2 RBRACE                                     {$$ = new_node("If",NULL); 
                                                                             node *aux = new_node("Block",NULL);
                                                                             add_childs(aux,1,$4);
                                                                             node *aux2 = new_node("Block",NULL);
                                                                             if($2){add_childs($$,3,$2,aux,aux2);};}

     |IF Expr LBRACE Statement_2 RBRACE ELSE LBRACE Statement_2 RBRACE      {$$ = new_node("If",NULL);
                                                                             node *aux = new_node("Block",NULL);
                                                                             add_childs(aux,1,$4);
                                                                             node *aux2 = new_node("Block",NULL);
                                                                             add_childs(aux2,1,$8);
                                                                             if($2){add_childs($$,3,$2,aux,aux2);}}


     |FOR LBRACE Statement_2 RBRACE                                         {$$ = new_node("For", NULL);
                                                                              node *aux = new_node("Block",NULL);
                                                                              add_childs(aux,1,$3);
                                                                             if($2){ add_childs($$,1,aux);}}

     |FOR Expr LBRACE Statement_2 RBRACE                                    {$$ = new_node("For", NULL);
                                                                              node *aux = new_node("Block",NULL);
                                                                              add_childs(aux,1,$4);
                                                                              if($2){add_childs($$,2,$2,aux);}}

     |RETURN                                                                {$$ = new_node("Return", NULL);}
     |RETURN Expr                                                           {$$ = new_node("Return", NULL);add_childs($$,1,$2);}

     |ParseArgs                                                             {$$ = new_node("ParseArgs", NULL); add_childs($$, 1, $1);}
     |FuncInvocation                                                        {$$ = new_node("Call", NULL);add_childs($$, 1, $1);}

     |PRINT LPAR Expr RPAR                                                  {$$ = new_node("Print", NULL); add_childs($$,1,$3);}
     |PRINT LPAR STRLIT RPAR                                                {$$ = new_node("Print", NULL); add_childs($$,1,new_node("StrLit",$3));}
     |error                                                                 {$$ = NULL;}
    ;

Statement_2:
     Statement SEMICOLON Statement_2                                        {if($$){$$ = $1; add_sibling($$,$3);}else{ $$ = $3;}}
    
     |                                                                      {$$ = NULL;}
     ;


ParseArgs:
     IDENTIFIER COMMA BLANKID ASSIGN PARSEINT LPAR CMDARGS LSQ Expr RSQ RPAR {$$ = new_node("Identifier", $1); add_sibling($$,$9);}
     |IDENTIFIER COMMA BLANKID ASSIGN PARSEINT LPAR error RPAR               {$$ = NULL;}
    ;

FuncInvocation:
     IDENTIFIER LPAR RPAR                                                   {$$ = new_node("Identifier", $1); }
     |IDENTIFIER LPAR Expr FuncInvocation_2 RPAR                            {$$ = new_node("Identifier", $1); add_sibling($$,$3);add_sibling($$,$4);}
     |IDENTIFIER LPAR error RPAR                                            {$$ = NULL;}     
    ;

FuncInvocation_2:
     COMMA Expr FuncInvocation_2                                            {$$ = $2; add_sibling($$,$3);}
     |                                                                      {$$ = NULL;}
     ;


Expr:
     Expr OR Expr                                                           {$$ = new_node("Or", NULL); add_childs($$,2,$1,$3);}
     |Expr AND Expr                                                         {$$ = new_node("And", NULL); add_childs($$,2,$1,$3);}

     |Expr LT Expr                                                          {$$ = new_node("Lt", NULL); add_childs($$,2,$1,$3);}
     |Expr GT Expr                                                          {$$ = new_node("Gt", NULL); add_childs($$,2,$1,$3);}
     |Expr EQ Expr                                                          {$$ = new_node("Eq", NULL); add_childs($$,2,$1,$3);}
     |Expr NE Expr                                                          {$$ = new_node("Ne", NULL); add_childs($$,2,$1,$3);}
     |Expr LE Expr                                                          {$$ = new_node("Le", NULL); add_childs($$,2,$1,$3);}
     |Expr GE Expr                                                          {$$ = new_node("Ge", NULL); add_childs($$,2,$1,$3);}

     |Expr PLUS Expr                                                        {$$ = new_node("Add", NULL); add_childs($$,2,$1,$3);}
     |Expr MINUS Expr                                                       {$$ = new_node("Sub", NULL); add_childs($$,2,$1,$3);}
     |Expr STAR Expr                                                        {$$ = new_node("Mul", NULL); add_childs($$,2,$1,$3);}
     |Expr DIV Expr                                                         {$$ = new_node("Div", NULL); add_childs($$,2,$1,$3);}
     |Expr MOD Expr                                                         {$$ = new_node("Mod", NULL); add_childs($$,2,$1,$3);}

     |NOT Expr %prec NOT                                                    {$$ = new_node("Not", NULL); add_childs($$,1,$2);} 
     |MINUS Expr %prec NOT                                                  {$$ = new_node("Minus", NULL); add_childs($$,1,$2);} 
     |PLUS Expr %prec NOT                                                   {$$ = new_node("Plus", NULL); add_childs($$,1,$2);} 

     |NATURAL                                                               {$$ = new_node("Natural", $1);}
     |DECIMAL                                                               {$$ = new_node("Decimal", $1);}
     |IDENTIFIER                                                            {$$ = new_node("Identifier",$1);}

     |FuncInvocation                                                        {$$ = new_node("Call",NULL); add_childs($$,1,$1);}
     |LPAR Expr RPAR                                                        {$$ = $2;}
     |LPAR error RPAR                                                       {$$ = NULL;}
    
     ;
%%


int main(int argc, char *argv[]) {
	if(argc==2){
		if(strcmp(argv[1],"-l")==0){
            flagl=1;
            flagt=0;
            yylex();
			
		}
		else if(strcmp(argv[1],"-t")==0){
			flagt=1;
			flagl=0;
            yyparse();
            
		}
        else if (strcmp(argv[1], "-s") == 0) {
            flagt=1;
			flagl=0;
            yyparse();
            if (!errorY) {
                symbol_table *global_table = create_symbol_table();
                register_symbols(program, global_table);
                print_all_tables(global_table);
                
            }
            print_tree(program, 0);
        }
	}
    else if(argc==1){
        flagt=1;
		flagl=0;
        yyparse();
    }
   


	free_tree(program);
    
    yylex_destroy(); /*------------------------------------------*/
    return 0;

	
}
