"""
generate_er_diagram.py — MindMetrics

Genera el diagrama Entidad-Relacion de la BD completa (25 tablas)
agrupado por subsistema, con FKs reales basadas en el esquema fisico.

Salida: docs/mindmetrics_er.png  (resolucion alta, listo para informe)
"""
from pathlib import Path
from graphviz import Digraph

OUT_DIR = Path(__file__).resolve().parent.parent / "docs"
OUT_DIR.mkdir(exist_ok=True)
OUT_FILE = OUT_DIR / "mindmetrics_er"

# Paleta por subsistema
COLOR = {
    "django":     "#E5E7EB",  # gris
    "rbac":       "#FDE68A",  # amarillo
    "axes":       "#FCA5A5",  # rojo claro
    "auth":       "#93C5FD",  # azul
    "otp":        "#A7F3D0",  # verde claro
    "form":       "#C4B5FD",  # violeta
    "dominio":    "#FBCFE8",  # rosa
    "catalogo":   "#FDBA74",  # naranja
}

def table(g, name, pk, cols, color, label_top=None):
    """Renderiza una tabla como nodo HTML."""
    rows = ""
    rows += f'<TR><TD BGCOLOR="{color}" PORT="pk"><B>{pk}</B>  PK</TD></TR>'
    for c in cols:
        rows += f'<TR><TD ALIGN="LEFT">{c}</TD></TR>'
    title = label_top or name
    html = (
        f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
        f'<TR><TD BGCOLOR="{color}"><B>{title}</B></TD></TR>'
        f'{rows}'
        f'</TABLE>>'
    )
    g.node(name, label=html)


dot = Digraph("MindMetrics_ER", format="png")
dot.attr(rankdir="LR", splines="spline", nodesep="0.4", ranksep="0.8",
         bgcolor="white", fontname="Helvetica")
dot.attr("node", shape="plaintext", fontname="Helvetica", fontsize="10")
dot.attr("edge", fontname="Helvetica", fontsize="9", color="#374151")

# =========================================================================
# CLUSTER 1 — Maquinaria Django
# =========================================================================
with dot.subgraph(name="cluster_django") as c:
    c.attr(label="Infraestructura Django", style="rounded,filled",
           fillcolor="#F9FAFB", fontsize="12")
    table(c, "django_migrations", "id",
          ["app", "name", "applied"], COLOR["django"])
    table(c, "django_content_type", "id",
          ["app_label", "model"], COLOR["django"])
    table(c, "django_session", "session_key",
          ["session_data", "expire_date"], COLOR["django"])
    table(c, "django_admin_log", "id",
          ["action_time", "object_id", "change_message",
           "content_type_id  FK", "user_id  FK"], COLOR["django"])

# =========================================================================
# CLUSTER 2 — RBAC (permisos)
# =========================================================================
with dot.subgraph(name="cluster_rbac") as c:
    c.attr(label="RBAC — Permisos y grupos", style="rounded,filled",
           fillcolor="#FFFBEB", fontsize="12")
    table(c, "auth_permission", "id",
          ["name", "codename", "content_type_id  FK"], COLOR["rbac"])
    table(c, "auth_group", "id", ["name"], COLOR["rbac"])
    table(c, "auth_group_permissions", "id",
          ["group_id  FK", "permission_id  FK"], COLOR["rbac"])

# =========================================================================
# CLUSTER 3 — django-axes
# =========================================================================
with dot.subgraph(name="cluster_axes") as c:
    c.attr(label="django-axes — Lockout y auditoria", style="rounded,filled",
           fillcolor="#FEF2F2", fontsize="12")
    table(c, "axes_accessattempt", "id",
          ["username", "ip_address", "failures_since_start",
           "attempt_time"], COLOR["axes"])
    table(c, "axes_accessattemptexpiration", "id",
          ["attempt_id  FK", "expires_at"], COLOR["axes"])
    table(c, "axes_accessfailurelog", "id",
          ["username", "ip_address", "attempt_time"], COLOR["axes"])
    table(c, "axes_accesslog", "id",
          ["username", "ip_address", "logout_time"], COLOR["axes"])

# =========================================================================
# CLUSTER 4 — AUTH (CustomUser)
# =========================================================================
with dot.subgraph(name="cluster_auth") as c:
    c.attr(label="AUTH_USER_MODEL  (usuarios.CustomUser)",
           style="rounded,filled", fillcolor="#EFF6FF", fontsize="12")
    table(c, "usuarios_customuser", "id",
          ["email  UNIQUE", "username", "password  (Argon2)",
           "is_2fa_enabled", "email_verified_at",
           "is_active", "is_staff", "is_superuser",
           "last_login", "date_joined"], COLOR["auth"],
          label_top="usuarios_customuser  ★")
    table(c, "usuarios_customuser_groups", "id",
          ["customuser_id  FK", "group_id  FK"], COLOR["auth"])
    table(c, "usuarios_customuser_user_permissions", "id",
          ["customuser_id  FK", "permission_id  FK"], COLOR["auth"])

# =========================================================================
# CLUSTER 5 — OTP (2FA)
# =========================================================================
with dot.subgraph(name="cluster_otp") as c:
    c.attr(label="django-otp — 2FA", style="rounded,filled",
           fillcolor="#ECFDF5", fontsize="12")
    table(c, "otp_totp_totpdevice", "id",
          ["user_id  FK", "name", "confirmed",
           "key  (secret TOTP)", "step", "digits"], COLOR["otp"])
    table(c, "otp_static_staticdevice", "id",
          ["user_id  FK", "name", "confirmed"], COLOR["otp"])
    table(c, "otp_static_statictoken", "id",
          ["device_id  FK", "token  (backup code)"], COLOR["otp"])

# =========================================================================
# CLUSTER 6 — Formulario captura
# =========================================================================
with dot.subgraph(name="cluster_form") as c:
    c.attr(label="Captura dataset (app formulario)", style="rounded,filled",
           fillcolor="#F5F3FF", fontsize="12")
    table(c, "formulario_datasetregistro", "id",
          ["nombre", "email  UNIQUE", "edad",
           "profesion", "created_at", "user_id  FK"], COLOR["form"])

# =========================================================================
# CLUSTER 7 — DOMINIO (managed=False)
# =========================================================================
with dot.subgraph(name="cluster_dominio") as c:
    c.attr(label="DOMINIO MindMetrics — 3NF (managed=False)",
           style="rounded,filled", fillcolor="#FDF2F8", fontsize="12")

    table(c, "usuario", "id_usuario",
          ["email  UNIQUE", "password", "nickname",
           "activo", "consentimiento_aceptado",
           "\"2FA_habilitado\""], COLOR["dominio"],
          label_top="usuario  ★")

    table(c, "emocion", "id_emocion",
          ["nombre_emocion"], COLOR["catalogo"])

    table(c, "tipo_recurso", "id_tipo_recurso",
          ["nombre_recurso"], COLOR["catalogo"])

    table(c, "evaluacion_inicial", "id_eval",
          ["id_usuario  FK", "edad", "genero",
           "estado_relacion", "situacion_trabajo",
           "hr_sueno", "hr_trabajo", "hr_pantalla",
           "hr_act_fis", "estres_laboral",
           "estres_academico", "estres_financ",
           "satisfaccion_laboral", "uso_sustancias",
           "dificultad_concentra", "cambio_emocional",
           "diagnostico_previo", "tratamiento_previo",
           "apoyo_percibido", "historial_panico",
           "historial_familiar"], COLOR["dominio"])

    table(c, "registro_emocional", "id_registro",
          ["id_usuario  FK", "id_emocion  FK",
           "fecha_registro", "nivel_riesgo  (ML)",
           "hr_sueno_dia", "hr_trabajo_dia",
           "hr_pantalla_dia", "hr_act_fis_dia",
           "estres_laboral_dia", "estres_academico_dia",
           "estres_financ_dia", "apoyo_percibido_dia",
           "autocuidado", "animo"], COLOR["dominio"])

    table(c, "recurso_apoyo", "id_recurso",
          ["id_tipo_recurso  FK", "titulo",
           "informacion", "imagen"], COLOR["dominio"])

    table(c, "presentacion_recurso", "(id_usuario,id_recurso,fecha)",
          ["id_usuario  FK", "id_recurso  FK",
           "fecha_presentacion"], COLOR["dominio"],
          label_top="presentacion_recurso  (PK compuesta)")


# =========================================================================
# EDGES (FOREIGN KEYS REALES)
# =========================================================================

# Django interno
dot.edge("django_admin_log", "django_content_type", label="content_type_id")
dot.edge("django_admin_log", "usuarios_customuser", label="user_id")

# RBAC
dot.edge("auth_permission", "django_content_type", label="content_type_id")
dot.edge("auth_group_permissions", "auth_group", label="group_id")
dot.edge("auth_group_permissions", "auth_permission", label="permission_id")

# axes
dot.edge("axes_accessattemptexpiration", "axes_accessattempt",
         label="attempt_id")

# CustomUser ↔ RBAC
dot.edge("usuarios_customuser_groups", "usuarios_customuser",
         label="customuser_id")
dot.edge("usuarios_customuser_groups", "auth_group", label="group_id")
dot.edge("usuarios_customuser_user_permissions", "usuarios_customuser",
         label="customuser_id")
dot.edge("usuarios_customuser_user_permissions", "auth_permission",
         label="permission_id")

# OTP → AUTH
dot.edge("otp_totp_totpdevice", "usuarios_customuser",
         label="user_id", color="#059669", penwidth="1.6")
dot.edge("otp_static_staticdevice", "usuarios_customuser",
         label="user_id", color="#059669", penwidth="1.6")
dot.edge("otp_static_statictoken", "otp_static_staticdevice",
         label="device_id", color="#059669", penwidth="1.6")

# Formulario → AUTH
dot.edge("formulario_datasetregistro", "usuarios_customuser",
         label="user_id", color="#7C3AED", penwidth="1.6")

# DOMINIO
dot.edge("evaluacion_inicial", "usuario",
         label="id_usuario  (ON DELETE CASCADE)",
         color="#BE185D", penwidth="1.8")
dot.edge("registro_emocional", "usuario",
         label="id_usuario  (ON DELETE RESTRICT)",
         color="#BE185D", penwidth="1.8")
dot.edge("registro_emocional", "emocion",
         label="id_emocion", color="#BE185D", penwidth="1.6")
dot.edge("recurso_apoyo", "tipo_recurso",
         label="id_tipo_recurso", color="#BE185D", penwidth="1.6")
dot.edge("presentacion_recurso", "usuario",
         label="id_usuario", color="#BE185D", penwidth="1.6")
dot.edge("presentacion_recurso", "recurso_apoyo",
         label="id_recurso", color="#BE185D", penwidth="1.6")

# Puente propuesto (Camino A — todavia NO existe)
dot.edge("usuarios_customuser", "usuario",
         label="usuario_dominio_id  (1-a-1 PROPUESTO)",
         style="dashed", color="#DC2626", penwidth="2.0",
         fontcolor="#DC2626")

# =========================================================================
# Render
# =========================================================================
out_path = dot.render(filename=str(OUT_FILE), cleanup=True)
print(f"OK — diagrama generado en: {out_path}")
