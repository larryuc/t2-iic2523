# ------------------------------------------------------------------------------------
# Pontificia Universidad Católica de Chile
# Escuela de Ingeniería — Departamento de Ciencia de la Computación
# Curso: IIC2523 - Sistemas Distribuidos
# Evaluación: Tarea 2 - Simulación de algoritmos de consenso (Raft)
#
# Archivo: database2.py
# Autor: Larry Andrés Uribe Araya
# ------------------------------------------------------------------------------------

class Database:
    """Base de datos simplificada exclusiva para Raft."""

    def __init__(self):
        self.data = {}

    # -------------------------------------------------------------------------
    def _normalize_key(self, key: str) -> str:
        """Normaliza claves reemplazando guiones bajos por espacios."""
        if not key:
            return key
        return key.replace("_", " ").strip()

    # -------------------------------------------------------------------------
    def apply_action(self, action: str) -> None:
        """Ejecuta una acción SET-, ADD- o DEL-."""
        if not action or "-" not in action:
            # print(f"[DEBUG][DB] Acción inválida: '{action}'")
            return

        parts = action.split("-", 2)
        op = parts[0].strip().upper()

        # --- SET ---
        if op == "SET" and len(parts) == 3:
            key = self._normalize_key(parts[1])
            value = parts[2].strip()

            # Limpieza previa si ya existe
            if key in self.data:
                # print(f"[DEBUG][DB] Limpieza previa: removiendo valor anterior de {key}")
                del self.data[key]

            # print(f"[DEBUG][DB] SET {key} = '{value}'")
            self.data[key] = value

        # --- ADD ---
        elif op == "ADD" and len(parts) == 3:
            key = self._normalize_key(parts[1])
            value = parts[2].strip()

            # Obtenemos el valor previo actual
            prev = self.data.get(key, "")
            # print(f"[DEBUG][DB] ADD detectado sobre '{key}' → previo='{prev}' nuevo='{value}'")

            # 🔧 FIX: Si el valor previo proviene de un SET posterior (no de una concatenación previa),
            # entonces el ADD debe iniciar una nueva concatenación y no extender el valor previo.
            # Detectamos esto cuando el valor previo NO termina con el valor añadido y
            # no hay espacio pendiente.
            if prev and not prev.strip().isdigit() and not prev.endswith(value):
                sep = " " if not prev.endswith(" ") else ""
                new_val = (prev + sep + value).strip()
            elif prev.strip().isdigit() and value.strip().isdigit():
                # Caso numérico
                new_val = str(int(prev) + int(value))
            else:
                # Caso general seguro
                sep = " " if prev and not prev.endswith(" ") else ""
                new_val = (prev + sep + value).strip()

            # print(f"[DEBUG][DB] ADD {key} += '{value}' → '{new_val}'")
            self.data[key] = new_val

        # --- DEL ---
        elif op == "DEL" and len(parts) >= 2:
            raw_key = parts[1].strip()
            normalized = self._normalize_key(raw_key)
            found = False
            for k in list(self.data.keys()):
                nk = self._normalize_key(k)
                if (
                    nk.lower() == normalized.lower()
                    or nk.lower().replace(" ", "_") == normalized.lower()
                    or nk.lower().replace("_", " ") == normalized.lower()
                ):
                    # print(f"[DEBUG][DB] DEL {k}")
                    del self.data[k]
                    found = True
                    break
            # if not found:
                # print(f"[DEBUG][DB] DEL falló: {raw_key} no existe")

        # else:
            # print(f"[DEBUG][DB] Acción desconocida: {action}")

    # -------------------------------------------------------------------------
    def log_value(self, var: str) -> str:
        key = self._normalize_key(var)
        val = self.data.get(key, "Variable no existe")
        # print(f"[DEBUG][DB] GET {key} = '{val}'")
        return val

    # -------------------------------------------------------------------------
    def snapshot(self) -> dict:
        # print(f"[DEBUG][DB] Snapshot: {self.data}")
        return dict(self.data)
