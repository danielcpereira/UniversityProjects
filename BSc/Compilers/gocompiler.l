/*
Daniel Pereira Nº 2021237092
Manuel Couto   Nº 2021233121
*/

%{
#include <stdio.h>
#include <string.h>
#include <stdlib.h> 

#include "y.tab.h"


#define YY_USER_ACTION { syn_line = line_num; syn_column = col_num; }
#define PASS_TOKEN() yylval.lexeme = strdup(yytext);

int print = 0;

int lex_line = 1, lex_column = 1;
int syn_line = -1, syn_column = -1;


char string_buffer[1024]; 
int buffer_pos = 0; 

int line_num = 1;          
int col_num = 1;  

int verifica ;          
int semicolon = 0;

int string = 0;

int saved_line_num;   
int saved_col_num;  

int flagl =  0;
extern int flagt;

extern int eof;

extern int errorY;

int check = 0;

void process_string_literal();

%}

%X COMMENT STRING

escape      [fnrt\\\"]
digit       [0-9]
letter      [a-zA-Z]
hex_digit   [0-9a-fA-F]
hexadecimal 0[xX]{hex_digit}+
comment     "//"[^\n]*
valid_octal 0[0-7]+
invalid_octal 0([0-7]*[8-9]+[0-7]*)+
decimal ([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?
identifier ("_"|{letter})({letter}|{digit}|"_")* 


reserved  	"break"|"case"|"chan"|"const"|"continue"|"default"|"defer"|"fallthrough"|"go"|"goto"|"import"|"interface"|"map"|"range"|"select"|"struct"|"switch"|"type"|"++"|"--"
semicolon   ";"
comma       ","
blankid     "_"
assign      "="
star        "*"
div         "/"
minus       "-"
plus        "+"
eq          "=="
ge          ">="
gt          ">"
lbrace      "{"
le          "<="
lpar        "("
lsq         "["
lt          "<"
mod         "%"
ne          "!="
not         "!"
and         "&&"
or          "||"
rbrace      "}"
rpar        ")"
rsq         "]"
package     "package"
return      "return"
else        "else"
for         "for"
if          "if"
var         "var"
int         "int"
float32     "float32"
bool        "bool"
string      "string"
print       "fmt.Println"
parseint    "strconv.Atoi"
func        "func"
cmdargs     "os.Args"




%%


(\r)?\n					      {if(print){check = 1;};if(flagl){ if(semicolon==1) printf("SEMICOLON\n"); semicolon=0;}; line_num++;col_num=1; if(semicolon==1 && flagt){PASS_TOKEN();semicolon=0;  return SEMICOLON; };  }
<INITIAL><<EOF>>			  {if(flagl){ if(semicolon==1) printf("SEMICOLON\n"); semicolon=0;}; eof=1;  if(semicolon==1 && flagt){PASS_TOKEN();semicolon = 0; return SEMICOLON; };  return 0 ;}





"\""                          { saved_line_num = line_num; saved_col_num = col_num;BEGIN(STRING); verifica=1; buffer_pos = 0; string_buffer[0] = '\0'; semicolon = 0; col_num += yyleng;} 
<STRING>"\\"{escape}          { string_buffer[buffer_pos++] = '\\'; string_buffer[buffer_pos++] = yytext[1]; string_buffer[buffer_pos] = '\0'; semicolon = 0; col_num += yyleng; }           
<STRING>"\\"                  { errorY = 1; printf("Line %d, column %d: invalid escape sequence (\\)\n", line_num , col_num); col_num+=yyleng;  semicolon=0;}
<STRING>\\[^fnrt\"\\]         {  errorY = 1;printf("Line %d, column %d: invalid escape sequence (\\%c)\n", line_num, col_num, yytext[1]); 
                                buffer_pos = 0;   string_buffer[0] = '\0'; verifica=0;  semicolon=0; col_num += yyleng;}

<STRING>(\r)?\n	              { errorY = 1; printf("Line %d, column %d: unterminated string literal\n", saved_line_num, saved_col_num); 
                                line_num++; col_num = 1; BEGIN(INITIAL); semicolon=0; }
<STRING>[^\"\\\n]+            { strcat(string_buffer, yytext); buffer_pos += yyleng; col_num += yyleng; } 
<STRING>\"                    { if(flagl){  if (verifica){ process_string_literal(); semicolon=1; };};BEGIN(INITIAL); col_num += yyleng; if(flagt && verifica ){semicolon = 1; string = 1; PASS_TOKEN(); char formatted_string[1024];strcpy(formatted_string, "\""); strcat(formatted_string, string_buffer); strcat(formatted_string, "\""); yytext=strdup(formatted_string); yylval.lexeme = strdup(formatted_string); if(print){string = 0;};if(check){string = 1;};return STRLIT;}} 
<STRING><<EOF>>               { errorY = 1; printf("Line %d, column %d: unterminated string literal\n",  saved_line_num, saved_col_num); 
                             verifica=0; semicolon=0; return 0; }



            

"/*"                          {BEGIN(COMMENT); saved_line_num = line_num;saved_col_num = col_num; col_num += yyleng; }
<COMMENT>"*/"                 {BEGIN (0);  col_num+=yyleng;}
<COMMENT><<EOF>>              {errorY = 1;printf("Line %d, column %d: unterminated comment\n", saved_line_num, saved_col_num); semicolon = 0; BEGIN 0; return 0 ;}
<COMMENT>(\r)?\n			  {if(flagl){ if(semicolon == 1) {  printf("SEMICOLON\n"); }};  line_num++; col_num=1; semicolon = 0;}      
<COMMENT>.                    {col_num +=yyleng; }


{comment}                     {if(flagl){ if(semicolon == 1) {printf("SEMICOLON\n"); }};  if(semicolon == 1 && flagt ) {  semicolon = 0;PASS_TOKEN(); return SEMICOLON;};  semicolon = 0;}



{semicolon}                   {if(flagl){ printf("SEMICOLON\n");}; col_num+=yyleng; semicolon=0;if(flagt){PASS_TOKEN(); return SEMICOLON; }}
{comma}	                      {if(flagl){ printf("COMMA\n");}; col_num+=yyleng; semicolon=0;    if(flagt){PASS_TOKEN(); return COMMA;}}
{blankid}                     {if(flagl){ printf("BLANKID\n");}; col_num+=yyleng; semicolon=0;  if(flagt){PASS_TOKEN(); return BLANKID;}}
{assign}	                  {if(flagl){ printf("ASSIGN\n");}; col_num+=yyleng; semicolon=0;   if(flagt){PASS_TOKEN(); return ASSIGN ; }}
{star}	                      {if(flagl){ printf("STAR\n");}; col_num+=yyleng; semicolon=0;     if(flagt){PASS_TOKEN(); return STAR; }}
{div}                         {if(flagl){ printf("DIV\n");}; col_num+=yyleng; semicolon=0;      if(flagt){PASS_TOKEN(); return DIV;}}
{minus}	                      {if(flagl){ printf("MINUS\n");}; col_num+=yyleng; semicolon=0;    if(flagt){PASS_TOKEN(); return MINUS; }}
{plus}                        {if(flagl){ printf("PLUS\n");}; col_num+=yyleng; semicolon=0;     if(flagt){PASS_TOKEN(); return PLUS; }}
{eq}	                      {if(flagl){ printf("EQ\n");}; col_num+=yyleng; semicolon=0;       if(flagt){PASS_TOKEN(); return EQ; }}
{ge}                          {if(flagl){ printf("GE\n");}; col_num+=yyleng; semicolon=0;       if(flagt){PASS_TOKEN(); return GE;}}
{gt}	                      {if(flagl){ printf("GT\n");}; col_num+=yyleng; semicolon=0;       if(flagt){PASS_TOKEN(); return GT;}}
{lbrace}	                  {if(flagl){ printf("LBRACE\n");}; col_num+=yyleng; semicolon=0;   if(flagt){PASS_TOKEN(); return LBRACE; }}
{le}                          {if(flagl){ printf("LE\n");}; col_num+=yyleng; semicolon=0;       if(flagt){PASS_TOKEN(); return LE; }}
{lpar}                        {if(flagl){ printf("LPAR\n");}; col_num+=yyleng; semicolon=0;     if(flagt){PASS_TOKEN(); return LPAR; }}
{lsq}		                  {if(flagl){ printf("LSQ\n");}; col_num+=yyleng; semicolon=0;      if(flagt){PASS_TOKEN(); return LSQ; }}
{lt}                          {if(flagl){ printf("LT\n");}; col_num+=yyleng; semicolon=0;       if(flagt){PASS_TOKEN(); return LT; }}
{mod}	                      {if(flagl){ printf("MOD\n");}; col_num+=yyleng; semicolon=0;      if(flagt){PASS_TOKEN(); return MOD; }}
{ne}	                      {if(flagl){ printf("NE\n");}; col_num+=yyleng; semicolon=0;       if(flagt){PASS_TOKEN(); return NE; }}
{not}	                      {if(flagl){ printf("NOT\n");}; col_num+=yyleng; semicolon=0;      if(flagt){PASS_TOKEN(); return NOT;}}
{and}	                      {if(flagl){ printf("AND\n");}; col_num+=yyleng; semicolon=0;      if(flagt){PASS_TOKEN(); return AND; }}
{or}	                      {if(flagl){ printf("OR\n");}; col_num+=yyleng; semicolon=0;       if(flagt){PASS_TOKEN(); return OR; }}
{rbrace}                      {if(flagl){ printf("RBRACE\n");}; col_num+=yyleng; semicolon=1;   if(flagt){PASS_TOKEN(); return RBRACE;}}
{rpar}		                  {if(flagl){ printf("RPAR\n");}; col_num+=yyleng; semicolon=1;     if(flagt){PASS_TOKEN(); return RPAR; }}
{rsq}	                      {if(flagl){ printf("RSQ\n");}; col_num+=yyleng; semicolon=1;      if(flagt){PASS_TOKEN(); return RSQ; }}
{package}                     {if(flagl){ printf("PACKAGE\n");}; col_num+=yyleng; semicolon=0;  if(flagt){PASS_TOKEN(); return PACKAGE;}}
{return}                      {if(flagl){ printf("RETURN\n");}; col_num+=yyleng; semicolon=1;   if(flagt){PASS_TOKEN(); return RETURN;}}
{else}	                      {if(flagl){ printf("ELSE\n");}; col_num+=yyleng; semicolon=0;     if(flagt){PASS_TOKEN(); return ELSE;}}
{for}	                      {if(flagl){ printf("FOR\n");}; col_num+=yyleng; semicolon=0;      if(flagt){PASS_TOKEN(); return FOR; }}
{if}                          {if(flagl){ printf("IF\n");}; col_num+=yyleng; semicolon=0;       if(flagt){PASS_TOKEN(); return IF;}}
{var}	                      {if(flagl){ printf("VAR\n");}; col_num+=yyleng; semicolon=0;      if(flagt){PASS_TOKEN(); return VAR; }}
{int}	                      {if(flagl){ printf("INT\n");}; col_num+=yyleng; semicolon=0;      if(flagt){PASS_TOKEN(); return INT; }}
{float32}	                  {if(flagl){ printf("FLOAT32\n");}; col_num+=yyleng; semicolon=0;  if(flagt){PASS_TOKEN(); return FLOAT32;  }}
{bool}	                      {if(flagl){ printf("BOOL\n");}; col_num+=yyleng; semicolon=0;     if(flagt){PASS_TOKEN(); return BOOL;}}
{string}                      {if(flagl){ printf("STRING\n");}; col_num+=yyleng; semicolon=0;   if(flagt){PASS_TOKEN(); return STRING1; }}
{print}	                      {print = 1;if(flagl){ printf("PRINT\n");}; col_num+=yyleng; semicolon=0;    if(flagt){PASS_TOKEN(); return PRINT; }}
{parseint}		              {if(flagl){ printf("PARSEINT\n");}; col_num+=yyleng; semicolon=0; if(flagt){PASS_TOKEN(); return PARSEINT;}}
{func}                        {if(flagl){ printf("FUNC\n");}; col_num+=yyleng; semicolon=0;     if(flagt){PASS_TOKEN(); return FUNC;}}
{cmdargs}	                  {if(flagl){ printf("CMDARGS\n");}; col_num+=yyleng; semicolon=0;  if(flagt){PASS_TOKEN(); return CMDARGS; }}
{reserved}					  {if(flagl){ printf("RESERVED(%s)\n", yytext);}; col_num+=yyleng; semicolon=0; if(flagt){PASS_TOKEN(); return CMDARGS; } }

{identifier}                  {if(flagl){ printf("IDENTIFIER(%s)\n", yytext);}; semicolon=1;  col_num+=yyleng;if(flagt){  PASS_TOKEN();return IDENTIFIER;}}
{valid_octal}                 {if(flagl){ printf("NATURAL(%s)\n",yytext);}; col_num += yyleng ; semicolon = 1;if(flagt){ PASS_TOKEN();return NATURAL;}}
{invalid_octal}               {errorY = 1;if(flagl){ printf("Line %d, column %d: invalid octal constant (%s)\n", line_num, col_num, yytext);}; col_num += yyleng; semicolon = 0;}
{digit}+                      {if(flagl){ printf("NATURAL(%s)\n", yytext);};semicolon=1;col_num+=yyleng;if(flagt){PASS_TOKEN();return NATURAL;  }}
{hexadecimal}                 {if(flagl){ printf("NATURAL(%s)\n", yytext);}; semicolon=1; col_num+=yyleng;if(flagt){PASS_TOKEN();return NATURAL; } }
{decimal}                     {if(flagl){ printf("DECIMAL(%s)\n", yytext);}; col_num += yyleng; semicolon = 1;if(flagt){ PASS_TOKEN();return DECIMAL;}}







" "|\t						  { col_num+=yyleng;}



.                             { printf("Line %d, column %d: illegal character (%c)\n", line_num,  col_num, yytext[0]); col_num+=yyleng;}


%%
 
extern int yylex();
void process_string_literal() {printf("STRLIT(\"%s\")\n", string_buffer); }



int yywrap() {return 1;}

void yyerror(char *s) {
    
    errorY = 1;

    if (eof == 1) {
        printf("Line %d, column %d: %s: %s\n", line_num + 1, 1, s, yytext);
        return; /*certo*/
    }
    
    int aux_col = syn_column;
   
    if(print && string) { aux_col = aux_col - strlen(yytext) + 1; string = 0;print = 0;}

    
    if(string){ aux_col = saved_col_num  ; string = 0; }
   
    /*normal case*/
    printf("Line %d, column %d: %s: %s\n", syn_line, aux_col, s, yytext);
    
    check = 0;
    print = 0;
}
