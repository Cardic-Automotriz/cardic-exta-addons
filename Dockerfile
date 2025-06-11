FROM odoo:17

USER root
RUN pip3 install boto3 && \
    mkdir -p /var/lib/odoo/.local/share/Odoo/assets && \
    mkdir -p /var/lib/odoo/.local/share/Odoo/filestore && \
    mkdir -p /var/lib/odoo/.local/share/Odoo/sessions && \
    chown -R odoo:odoo /var/lib/odoo/.local/share/Odoo && \
    chmod -R 755 /var/lib/odoo/.local/share/Odoo

USER odoo