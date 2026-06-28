Para realizar el setup, la ejecucion de la pipeline y los test deberia vale con:  
Instalamos make  
```bash
sudo apt-get update && sudo apt-get install make
```

Instalamos dependencias de sistema, creamos el entorno virtual de python y instalamos dependencias de python  
```bash
make full_init
```

Si no se encuentra el binario de poetry, relogear usuario:
```bash
su $USER
```

Activamos el nuevo entorno vitual python recien creado
```bash
source .venv/bin/activate
```

Ejecutamos metadata driven transfo
```bash
make local_run
```

Para ejecutar los reportes de data quality del punto 5
```bash
make pytest
```

Para levantar la instancia de airflow del punto 6-7
```bash
make airflow_run
```