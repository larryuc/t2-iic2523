# ------------------------------------------------------------------------------------
# Pontificia Universidad Católica de Chile
# Escuela de Ingeniería – Departamento de Ciencia de la Computación
# Curso: IIC2523 - Sistemas Distribuidos
# Evaluación: Tarea 2 - Simulación de algoritmos de consenso (Raft)
#
# Archivo: raft.py
# Autor: Larry Andrés Uribe Araya
# ------------------------------------------------------------------------------------

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from database2 import Database


@dataclass
class NodeState:
    active: bool = True
    timeout: int = 0
    term: int = 0
    log: List[Tuple[int, str]] = field(default_factory=list)


class RaftSimulator:
    """Simulador detallado de Raft con depuración completa."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.db = Database()
        self.nodes: Dict[str, NodeState] = {}
        self.leader: Optional[str] = None
        self.term: int = 0
        self.commit_index: int = 0
        self.last_applied: int = 0

    @staticmethod
    def _clean(line: str) -> str:
        if "#" in line:
            line = line.split("#", 1)[0]
        return line.strip()

    @staticmethod
    def _normalize_key(cmd: str) -> str:
        if not cmd:
            return cmd
        parts = cmd.split("-", 2)
        if len(parts) >= 2:
            parts[1] = parts[1].strip()
        if len(parts) == 3:
            parts[2] = parts[2].strip()
        return "-".join(parts)

    def _active_ids(self) -> List[str]:
        return [nid for nid, st in self.nodes.items() if st.active]

    def _majority(self) -> int:
        active = len(self._active_ids())
        maj = (active // 2) + 1 if active > 0 else 1
    # print(f"[DEBUG] Calculando mayoría: activos={active} → mayoría={maj}")
        return maj

      # -------------------------------------------------------------------------
  # -------------------------------------------------------------------------
       # -------------------------------------------------------------------------
    def _pick_leader(self) -> None:
        # print("\n[DEBUG] ===== ELECCIÓN DE NUEVO LÍDER =====")
        activos = self._active_ids()
    # print(f"[DEBUG] Nodos activos: {activos}")

        if not activos:
            # print("[DEBUG] ❌ No hay nodos activos, no se elige líder.")
            self.leader = None
            return

        # 🧮 Selección de líder con mayor term, largo de log, menor timeout
        candidato = max(
            activos,
            key=lambda nid: (
                self.nodes[nid].log[-1][0] if self.nodes[nid].log else 0,
                len(self.nodes[nid].log),
                -self.nodes[nid].timeout
            )
        )

        self.term += 1
        self.leader = candidato
        self.nodes[self.leader].term = self.term
    # print(f"[DEBUG] 🏆 Líder elegido: {self.leader} (term={self.term})")

        maj_total = self._majority()
        max_len = max((len(self.nodes[nid].log) for nid in activos), default=0)
        committed: List[Tuple[int, str]] = []

    # print(f"[DEBUG] Iniciando reconstrucción de log común, longitud máxima={max_len}")

        for i in range(max_len):
            acciones = {}
            for nid in activos:
                st = self.nodes[nid]
                if len(st.log) > i:
                    term, accion = st.log[i]
                    acciones[accion] = acciones.get(accion, 0) + 1
                    # print(f"[DEBUG] Nodo {nid} → log[{i}]={st.log[i]}")
            if not acciones:
                # print(f"[DEBUG] ❌ Sin acciones en índice {i}, se detiene consenso")
                break

            best, votos = max(acciones.items(), key=lambda x: x[1])
            # print(f"[DEBUG] Prefijo {i}: acción más votada='{best}' con {votos}/{maj_total}")

            if votos >= maj_total:
                terminos = [
                    self.nodes[nid].log[i][0]
                    for nid in activos
                    if len(self.nodes[nid].log) > i and self.nodes[nid].log[i][1] == best
                ]
                term_comun = max(set(terminos), key=terminos.count) if terminos else self.term
                committed.append((term_comun, best))
                # print(f"[DEBUG] ✅ Acción '{best}' aceptada con término común={term_comun}")
            else:
                # print(
                # f"[DEBUG] ⚠️ Acción '{best}' no alcanza mayoría ({votos}/{maj_total}),
                # se detiene")
                break

        # 🔧 FIX 1: si el commit previo es mayor, truncar en vez de extender
        if self.commit_index > len(committed):
            # print(f"[DEBUG] Truncando commits antiguos a índice {self.commit_index}")
            committed = committed[:self.commit_index]

        prev_log = self.nodes[self.leader].log.copy() if self.leader in self.nodes else []
    # print(f"[DEBUG] Log previo del líder {self.leader}: {prev_log}")
    # print(f"[DEBUG] Log nuevo comprometido: {committed}")

        # Consolidación segura
        final_log = []
        for entry in committed:
            if entry not in final_log:
                final_log.append(entry)
        for entry in prev_log:
            if entry not in final_log:
                final_log.append(entry)

    # print(f"[DEBUG] Log final consolidado → {final_log}")

        # Sincronizar todos los nodos
        for nid, st in self.nodes.items():
            st.log = final_log.copy()
            # print(f"[DEBUG] Nodo {nid} sincronizado → log={st.log}")

        # ------------------------------------------------------------------
        # 🔧 FIX FINAL: forzar reaplicación de BD si el log se acorta
        # ------------------------------------------------------------------
        if final_log != prev_log:
            # print("[DEBUG][DB] Log comprometido cambió → reaplicando BD desde cero")
            self.db = Database()
            for term, act in final_log:
                # print(f"[DEBUG][DB] Aplicando a BD: ({term}, {act})")
                self.db.apply_action(act)
        elif len(final_log) < len(prev_log):
            # print("[DEBUG][DB] ⚠️ Log truncado detectado → reaplicando BD (forzado)")
            self.db = Database()
            for term, act in final_log:
                # print(f"[DEBUG][DB] Reaplicando tras truncamiento: ({term}, {act})")
                self.db.apply_action(act)
        else:
            # print("[DEBUG][DB] Log comprometido sin cambios → se conserva estado BD actual")
            pass

        self.commit_index = len(final_log)
        self.last_applied = self.commit_index
    # print(f"[DEBUG][DB] Snapshot final tras elección: {self.db.snapshot()}")
    # print(f"[DEBUG] Prefijo comprometido aplicado: {self.db.snapshot()}")
    # print("[DEBUG] ===== FIN ELECCIÓN LÍDER =====\n")

        self._recompute_commit_and_apply()

    # -------------------------------------------------------------------------
    def _event_start(self, nid: str) -> None:
        # print(f"[EVENT] Start de nodo {nid}")
        if nid not in self.nodes:
            self.nodes[nid] = NodeState(True, 0, 0)
        else:
            self.nodes[nid].active = True

        if self.leader and self.leader in self.nodes:
            leader_log = self.nodes[self.leader].log
            if leader_log and self.nodes[nid].log != leader_log:
                # print(f"[DEBUG] Nodo {nid} sincronizado con log líder {self.leader}")
                self.nodes[nid].log = leader_log.copy()
        else:
            self._pick_leader()

        self._recompute_commit_and_apply()

    def _event_stop(self, nid: str) -> None:
        # print(f"[EVENT] Stop de nodo {nid}")
        if nid in self.nodes:
            was_leader = nid == self.leader
            self.nodes[nid].active = False
            if was_leader:
                # print("[DEBUG] 🚫 El líder se detuvo. Reelección forzada.")
                self._pick_leader()
                if self.leader:
                    self._recompute_commit_and_apply()

    # -------------------------------------------------------------------------
    def _send(self, action: str) -> None:
        # print(f"[SEND] Acción enviada: {action}")
        action = self._normalize_key(action)
        if not self.leader or not self.nodes.get(self.leader, NodeState()).active:
            # print("[DEBUG] ⚠️ No hay líder activo. Acción ignorada.")
            return
        st = self.nodes[self.leader]
        st.log.append((self.term, action))
    # print(f"[DEBUG] Log del líder actualizado: {st.log}")

    def _spread(self, targets: Optional[List[str]]) -> None:
        # print(f"[SPREAD] Iniciando propagación → {targets}")
        if not self.leader or self.leader not in self.nodes:
            # print("[DEBUG] ❌ No hay líder válido para spread.")
            return
        if not self.nodes[self.leader].active:
            # print("[DEBUG] ⚠️ El líder actual está inactivo.")
            return

        leader_log = self.nodes[self.leader].log
        if not leader_log:
            # print("[DEBUG] ℹ️ Log líder vacío, nada que propagar.")
            return

        dests = (
            [nid for nid in self._active_ids() if nid != self.leader]
            if not targets
            else [t for t in targets if t in self._active_ids() and t != self.leader]
        )

    # print(f"[DEBUG] Propagando log {leader_log} hacia {dests}")
        for d in dests:
            self.nodes[d].log = leader_log.copy()
            # print(f"[DEBUG] Nodo {d} actualizado con log: {self.nodes[d].log}")

        self._recompute_commit_and_apply()

    def _event_log(self, var: str, out: List[str]) -> None:
        # print(f"[LOG] Consultando variable '{var}'")
        self._recompute_commit_and_apply()
        val = self.db.log_value(var)
        out.append(f"{var}={val}")

    # -------------------------------------------------------------------------
    def _recompute_commit_and_apply(self) -> None:
        # print(f"[DEBUG] === RECOMPUTE COMMIT === líder={self.leader}")
        if not self.leader or self.leader not in self.nodes:
            # print("[DEBUG] ❌ No hay líder válido.")
            return

        leader_state = self.nodes[self.leader]
        if not leader_state.active:
            # print("[DEBUG] ⚠️ El líder está inactivo.")
            return

        leader_log = leader_state.log
        majority = self._majority()
        activos = self._active_ids()
        new_commit = self.commit_index

        for i, (term_entry, action) in enumerate(leader_log):
            count = sum(
                1 for nid in activos
                if len(self.nodes[nid].log) > i and self.nodes[nid].log[i][1] == action
            )
            # print(
            # f"[DEBUG] Entrada {i}: acción={action}, term={term_entry}, replicada en
            # {count} nodos")
            if count >= majority:
                new_commit = i + 1
            else:
                break

        if new_commit > self.commit_index:
            # print(f"[DEBUG] 🌀 Commit actualizado: {self.commit_index} → {new_commit}")
            self.commit_index = new_commit
            self.last_applied = new_commit
            # print("[DEBUG] 🔁 Reaplicando BD (desde cero):")
            self.db = Database()
            for _, act in leader_log[:self.commit_index]:
                # print(f"    [APPLY] {act}")
                self.db.apply_action(act)
            # print(f"[DEBUG][DB] Snapshot: {self.db.snapshot()}")
        else:
            # print(f"[DEBUG] ℹ️ Commit ya está actualizado en {self.commit_index}")
            pass
    # print(f"[DEBUG] FIN commit_index={self.commit_index}")

    # -------------------------------------------------------------------------
    def run(self) -> Tuple[List[str], Dict[str, str]]:
        # print(f"[RUN] Ejecutando archivo de entrada: {self.path}")
        with open(self.path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
        lines = [self._clean(x) for x in raw_lines if self._clean(x)]
        out: List[str] = []
        if not lines:
            # print("[RUN] ⚠️ Archivo vacío.")
            return out, self.db.snapshot()

        node_specs = [x.strip() for x in lines[0].split(";") if x.strip()]
    # print(f"[INIT] Nodos iniciales: {node_specs}")
        for tok in node_specs:
            if "," in tok:
                nid, t = tok.split(",", 1)
                try:
                    timeout = int(t)
                except ValueError:
                    timeout = 0
            else:
                nid, timeout = tok, 0
            self.nodes[nid] = NodeState(True, timeout, 0)
            # print(f"[INIT] Nodo {nid} creado (timeout={timeout})")

        self._pick_leader()
        self._recompute_commit_and_apply()

        for line in lines[1:]:
            # print(f"[EVENT] Procesando línea: {line}")
            if line.startswith("Send;"):
                self._send(line.split(";", 1)[1].strip())
            elif line.startswith("Spread;"):
                inside = line.split(";", 1)[1].strip().strip("[]")
                targets = [t.strip() for t in inside.split(",") if t.strip()]
                self._spread(targets)
            elif line.startswith("Start;"):
                self._event_start(line.split(";", 1)[1].strip())
            elif line.startswith("Stop;"):
                self._event_stop(line.split(";", 1)[1].strip())
            elif line.startswith("Log;"):
                self._event_log(line.split(";", 1)[1].strip(), out)

        self._recompute_commit_and_apply()
    # print(f"[RUN] ✅ Finalizado. Estado BD final: {self.db.snapshot()}")
        return out, self.db.snapshot()
