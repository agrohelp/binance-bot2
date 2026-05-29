# core/watchdog.py

def watchdog_candle_freeze(df, logger, tf_name="4H"):
    """
    Wykrywa zatrzymanie świec (brak nowych danych).
    Zwraca True jeśli OK, False jeśli świeca stoi.
    """

    if len(df) < 3:
        logger.warning(f"{tf_name}: Za mało świec do watchdog")
        return False

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # 1) Czy timestamp się zmienił?
    if last["open_time"] == prev["open_time"]:
        logger.error(f"{tf_name}: WATCHDOG — świeca stoi w miejscu! Brak nowych danych.")
        return False

    # 2) Czy świeca jest nienaturalnie długa (np. 4H trwa 10h)?
    expected_ms = 4 * 60 * 60 * 1000
    delta = last["open_time"] - prev["open_time"]

    if delta > expected_ms * 1.5:
        logger.error(f"{tf_name}: WATCHDOG — przerwa między świecami {delta} ms (za duża).")
        return False

    return True
