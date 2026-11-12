"""Arranca y para el scheduler y comprueba que registra las dos tareas
(actualización horaria y descarga diaria) con el horario esperado, sin
ejecutarlas de verdad (no debe llamar a Yahoo Finance)."""
from app.jobs import scheduler as scheduler_mod


def test_iniciar_scheduler_registra_las_dos_tareas():
    try:
        scheduler_mod.iniciar_scheduler()

        ids = {job.id for job in scheduler_mod.scheduler.get_jobs()}
        assert ids == {"actualizacion_horaria", "descarga_diaria", "vigilar_descarga"}

        job_diaria = scheduler_mod.scheduler.get_job("descarga_diaria")
        assert str(job_diaria.trigger.timezone) == "Europe/Madrid"
    finally:
        scheduler_mod.detener_scheduler()


def test_detener_scheduler_lo_deja_parado():
    scheduler_mod.iniciar_scheduler()
    scheduler_mod.detener_scheduler()
    assert scheduler_mod.scheduler.running is False
