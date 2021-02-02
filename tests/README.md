# test folder

# Download the tests from the NextCloud/iSanXoT/tests


___
## example 1
```
0.2.3
```

+ sanxot: The "emergencyvariance" has been changed.
In the case the maximum iterations are reached (see -m), force the provided variance by the user. Default 0.0

Te respondo: de ninguna manera te compliques haciendo programas independientes ni nada de eso!! Eso es un berenjenal, vamos a buscar la sencillez. La idea es que los módulos de sanxot sean suficientemente robustos internamente para no tener que controlar su funcionamiento desde fuera. Tienen que ser módulos capaces de funcionar de forma independiente. Lo único que necesitamos es que los módulos sean capaces de poner una varianza especificada previamente por el usuario cuando se alcanza un número máximo de iteraciones, y sanseacabó. Ojo, esta varianza especificada por el usuario no es lo mismo que la varianza fija que se puede forzar por el usuario, es una cosa diferente.
	Es decir, tendríamos tres parámetros: 
	-v, que fuerza una varianza fija sin hacer el ajuste
	-m, que establece el número máximo de iteraciones
	-w (por ejemplo), que establecería la varianza que forzaría el programa cuando se alcanzase el número máximo de iteraciones establecido por –m. El valor por defecto sería 0, es decir si no se pone nada, la varianza se pone a cero cuando se alcanza m.

	Cuando se aplica –v, los otros parámetros no se usan, o sea v “overrides” m y w. 
	En nuestro workflow de isanxot, no haría falta poner –w, ya que usaríamos el valor por defecto de cero, y pondríamos –m=600 en TODOS los casos donde se use un ajuste iterativo (kalibrate y sanxot, creo que no hay más módulos que lo hagan, no?). Es una solución relativamente sencilla y muy robusta.

1. Example experiment:

S:\U_Proteomica\UNIDAD\DatosCrudos\Jose_Antonio_Enriquez\MutanteCOX7A1\ZF\29_Oct_2020\COX7A1_ZF\iSanXoT_v021_2

"C:\Users\jmrodriguezc\iSanXoT\0.2\python\tools\python.exe" "S:\U_Proteomica\UNIDAD\DatosCrudos\jmrodriguezc\projects\iSanXoT/wfs/../src/SanXoT/sanxot.py" -g -b -s  -d "S:\U_Proteomica\UNIDAD\DatosCrudos\Jose_Antonio_Enriquez\MutanteCOX7A1\ZF\29_Oct_2020\COX7A1_ZF\iSanXoT_v021_2/jobs/heart_S/protein2proteinall_combData.tsv" -r "S:\U_Proteomica\UNIDAD\DatosCrudos\Jose_Antonio_Enriquez\MutanteCOX7A1\ZF\29_Oct_2020\COX7A1_ZF\iSanXoT_v021_2/jobs/heart_S/protein2proteinall_combRels.tsv" -z "S:\U_Proteomica\UNIDAD\DatosCrudos\Jose_Antonio_Enriquez\MutanteCOX7A1\ZF\29_Oct_2020\COX7A1_ZF\iSanXoT_v021_2/jobs/heart_S/protein2proteinall_outStats.tsv" -L "S:\U_Proteomica\UNIDAD\DatosCrudos\Jose_Antonio_Enriquez\MutanteCOX7A1\ZF\29_Oct_2020\COX7A1_ZF\iSanXoT_v021_2/jobs/heart_S/protein2proteinall_variance.txt" -a "protein2proteinall" -m "600"

