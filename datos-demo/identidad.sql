-- Generado por datos-demo/generar.py: no editar a mano.
SET NOCOUNT ON;
GO

-- empresas: 15
MERGE dbo.empresas AS t
USING (VALUES
  ('415a4da4-15b5-578b-880d-393afbf9ad5d', '900100001-1', 'Soluciones Andinas S.A.S.', 'Tecnología', 'https://empresa01.ejemplo.test', NULL),
  ('8aef2e0a-6ab9-5915-84f7-b50888b27ba2', '900100002-9', 'Café del Valle Export S.A.S.', 'Alimentos', 'https://empresa02.ejemplo.test', NULL),
  ('21549906-47ab-55d0-a72a-4ad669f5e8c3', '900100003-6', 'Logística Pacífico Ltda', 'Logística', 'https://empresa03.ejemplo.test', NULL),
  ('13cf73b3-1171-59d1-bb55-815d9c55ce34', '900100004-3', 'Construcciones Aurora S.A.S.', 'Construcción', 'https://empresa04.ejemplo.test', NULL),
  ('5e8886b4-f066-556b-bf3b-57d6d5f48521', '900100005-0', 'Textiles del Caribe S.A.S.', 'Textil', 'https://empresa05.ejemplo.test', NULL),
  ('c5033e3f-13c3-5f62-9999-a303568b0800', '900100006-8', 'AgroFuturo Colombia S.A.S.', 'Agro', 'https://empresa06.ejemplo.test', NULL),
  ('fd37774d-e7d9-5b26-a856-e9513714a8fa', '900100007-5', 'Energía Verde Andina S.A.S.', 'Energía', 'https://empresa07.ejemplo.test', NULL),
  ('483b6650-695d-500d-9d0b-958eda5d01ea', '900100008-2', 'Salud Integral del Centro S.A.S.', 'Salud', 'https://empresa08.ejemplo.test', NULL),
  ('077e07aa-674d-581c-abc5-66c53a150952', '900100009-1', 'Educación Digital S.A.S.', 'Educación', 'https://empresa09.ejemplo.test', NULL),
  ('355cb4e6-7cff-5c0d-8893-6d7d339b7368', '900100010-8', 'Turismo Cóndor S.A.S.', 'Turismo', 'https://empresa10.ejemplo.test', NULL),
  ('b79937d6-a7ec-5897-812f-761f91254b2f', '900100011-5', 'Muebles Roble S.A.S.', 'Mobiliario', 'https://empresa11.ejemplo.test', NULL),
  ('a5ecfb5d-0671-5bb6-a5e1-5c227c7f9ecd', '900100012-2', 'Editorial Horizonte S.A.S.', 'Editorial', 'https://empresa12.ejemplo.test', NULL),
  ('2f59ba7e-cc6d-5c00-9d36-1c06b57f690a', '900100013-1', 'Farmacéutica del Sur S.A.S.', 'Farmacéutico', 'https://empresa13.ejemplo.test', NULL),
  ('0799143f-ebe6-5395-8d69-2837276f7c49', '900100014-7', 'MetalMecánica Titán S.A.S.', 'Manufactura', 'https://empresa14.ejemplo.test', NULL),
  ('5e4eec28-eeb8-58e9-bc1b-31f6f886acd0', '900100015-4', 'Cosmética Natural S.A.S.', 'Cosmética', 'https://empresa15.ejemplo.test', NULL)
) AS s (id, nit, razon_social, sector, sitio_web, logo_url)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.nit = s.nit, t.razon_social = s.razon_social, t.sector = s.sector, t.sitio_web = s.sitio_web, t.logo_url = s.logo_url
WHEN NOT MATCHED THEN INSERT (id, nit, razon_social, sector, sitio_web, logo_url) VALUES (s.id, s.nit, s.razon_social, s.sector, s.sitio_web, s.logo_url);
GO

-- usuarios: 40
MERGE dbo.usuarios AS t
USING (VALUES
  ('a177e696-49b4-5d09-abde-2d59bd1e7a02', 'ana.rios01@ejemplo.test', 'Ana María Ríos', 'sin-acceso-datos-demo', 'expositor', '415a4da4-15b5-578b-880d-393afbf9ad5d', 1, 1, '2026-11-01 13:07:00', '2026-11-01 13:07:00'),
  ('d79f291a-472f-50b0-9a29-4459030ba085', 'carlos.perez02@ejemplo.test', 'Carlos Pérez', 'sin-acceso-datos-demo', 'expositor', '8aef2e0a-6ab9-5915-84f7-b50888b27ba2', 1, 1, '2026-11-01 13:14:00', '2026-11-01 13:14:00'),
  ('627b22d8-06a4-578d-a530-6dc2023a9161', 'laura.gomez03@ejemplo.test', 'Laura Gómez', 'sin-acceso-datos-demo', 'expositor', '21549906-47ab-55d0-a72a-4ad669f5e8c3', 1, 1, '2026-11-01 13:21:00', '2026-11-01 13:21:00'),
  ('7c2e3120-fae3-57a6-a41c-b2ec72fe95be', 'diego.ruiz04@ejemplo.test', 'Diego Ruiz', 'sin-acceso-datos-demo', 'expositor', '13cf73b3-1171-59d1-bb55-815d9c55ce34', 1, 1, '2026-11-01 13:28:00', '2026-11-01 13:28:00'),
  ('ddd244ae-1f98-5dca-9159-1768a3be5469', 'sofia.martinez05@ejemplo.test', 'Sofía Martínez', 'sin-acceso-datos-demo', 'expositor', '5e8886b4-f066-556b-bf3b-57d6d5f48521', 1, 1, '2026-11-01 13:35:00', '2026-11-01 13:35:00'),
  ('6563dc18-6925-5bf6-b6b5-c4346f0d0695', 'andres.ramirez06@ejemplo.test', 'Andrés Ramírez', 'sin-acceso-datos-demo', 'expositor', 'c5033e3f-13c3-5f62-9999-a303568b0800', 1, 1, '2026-11-01 13:42:00', '2026-11-01 13:42:00'),
  ('198cce25-3f14-535f-b08e-eda81fe5214b', 'paula.torres07@ejemplo.test', 'Paula Torres', 'sin-acceso-datos-demo', 'expositor', 'fd37774d-e7d9-5b26-a856-e9513714a8fa', 1, 1, '2026-11-01 13:49:00', '2026-11-01 13:49:00'),
  ('cd34c792-8f86-5f1b-827c-340492b1cbf9', 'julian.castro08@ejemplo.test', 'Julián Castro', 'sin-acceso-datos-demo', 'expositor', '483b6650-695d-500d-9d0b-958eda5d01ea', 1, 1, '2026-11-01 13:56:00', '2026-11-01 13:56:00'),
  ('832ed401-4b38-5749-a3f6-2ce03953d45d', 'valentina.ortiz09@ejemplo.test', 'Valentina Ortiz', 'sin-acceso-datos-demo', 'expositor', '077e07aa-674d-581c-abc5-66c53a150952', 1, 1, '2026-11-01 14:03:00', '2026-11-01 14:03:00'),
  ('e0dfa9d1-3e16-5daf-9197-bb4a47f04af0', 'felipe.herrera10@ejemplo.test', 'Felipe Herrera', 'sin-acceso-datos-demo', 'expositor', '355cb4e6-7cff-5c0d-8893-6d7d339b7368', 1, 1, '2026-11-01 14:10:00', '2026-11-01 14:10:00'),
  ('09e7aee2-8f6d-5cd1-a53a-ff6794cb96ff', 'mariana.silva11@ejemplo.test', 'Mariana Silva', 'sin-acceso-datos-demo', 'expositor', 'b79937d6-a7ec-5897-812f-761f91254b2f', 1, 1, '2026-11-01 14:17:00', '2026-11-01 14:17:00'),
  ('0644d343-d855-5112-ad4d-72dd22b0316c', 'sebastian.vargas12@ejemplo.test', 'Sebastián Vargas', 'sin-acceso-datos-demo', 'expositor', 'a5ecfb5d-0671-5bb6-a5e1-5c227c7f9ecd', 1, 1, '2026-11-01 14:24:00', '2026-11-01 14:24:00'),
  ('a778c573-211e-58a2-becd-e58bfbd9155d', 'camila.rojas13@ejemplo.test', 'Camila Rojas', 'sin-acceso-datos-demo', 'expositor', '2f59ba7e-cc6d-5c00-9d36-1c06b57f690a', 1, 1, '2026-11-01 14:31:00', '2026-11-01 14:31:00'),
  ('2aab8617-393a-56ab-aee3-d28e1eb093e6', 'daniel.molina14@ejemplo.test', 'Daniel Molina', 'sin-acceso-datos-demo', 'expositor', '0799143f-ebe6-5395-8d69-2837276f7c49', 1, 1, '2026-11-01 14:38:00', '2026-11-01 14:38:00'),
  ('26d4c3ee-5017-5c37-b5d5-d8d4de5cf9a9', 'natalia.suarez15@ejemplo.test', 'Natalia Suárez', 'sin-acceso-datos-demo', 'expositor', '5e4eec28-eeb8-58e9-bc1b-31f6f886acd0', 1, 1, '2026-11-01 14:45:00', '2026-11-01 14:45:00'),
  ('186532f0-d614-5680-8cfe-4177869fba67', 'juan.mejia16@ejemplo.test', 'Juan Pablo Mejía', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 14:52:00', '2026-11-01 14:52:00'),
  ('67aa2594-cb2e-5801-b731-5cbf8504897e', 'maria.londono17@ejemplo.test', 'María José Londoño', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 14:59:00', '2026-11-01 14:59:00'),
  ('6fa7aed3-f33b-54fe-82b6-2fd72721bea7', 'santiago.ospina18@ejemplo.test', 'Santiago Ospina', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 15:06:00', '2026-11-01 15:06:00'),
  ('61770e1d-e345-5165-b7e8-92cbbe0ae957', 'diana.ruiz19@ejemplo.test', 'Diana Carolina Ruiz', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 15:13:00', '2026-11-01 15:13:00'),
  ('e1192882-1157-5928-8f4e-b907cad0c35e', 'alejandro.gil20@ejemplo.test', 'Alejandro Gil', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 15:20:00', '2026-11-01 15:20:00'),
  ('27c894cf-bff3-501a-a842-be2b6b0d7f74', 'isabella.correa21@ejemplo.test', 'Isabella Correa', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 15:27:00', '2026-11-01 15:27:00'),
  ('653fa7ab-7f55-5b9d-9362-5627dc133163', 'mateo.restrepo22@ejemplo.test', 'Mateo Restrepo', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 15:34:00', '2026-11-01 15:34:00'),
  ('5704d7e2-0919-5356-a2c7-6f6bcc8eda45', 'sara.alvarez23@ejemplo.test', 'Sara Álvarez', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 15:41:00', '2026-11-01 15:41:00'),
  ('49d10a81-ff48-573a-ba6d-a66a60c163b4', 'samuel.jimenez24@ejemplo.test', 'Samuel Jiménez', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 15:48:00', '2026-11-01 15:48:00'),
  ('4b8d9fff-e783-55b7-a98d-f67706ed6000', 'manuela.duarte25@ejemplo.test', 'Manuela Duarte', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 15:55:00', '2026-11-01 15:55:00'),
  ('6088a3bf-51ad-5f13-b835-c3a4c59f74f3', 'emilio.salazar26@ejemplo.test', 'Emilio Salazar', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 16:02:00', '2026-11-01 16:02:00'),
  ('a016b6d7-8a58-58a0-96aa-c5d7cb348ffd', 'julieta.pena27@ejemplo.test', 'Julieta Peña', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 16:09:00', '2026-11-01 16:09:00'),
  ('df886d3c-421b-56eb-a26a-2b5df2cb1e2b', 'tomas.cardenas28@ejemplo.test', 'Tomás Cárdenas', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 16:16:00', '2026-11-01 16:16:00'),
  ('964db46d-079e-53a5-919b-99c3ff407d5c', 'maria.cano29@ejemplo.test', 'María Fernanda Cano', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 16:23:00', '2026-11-01 16:23:00'),
  ('92bf56c0-70d9-5d1d-adb9-533e0dada1c4', 'nicolas.rincon30@ejemplo.test', 'Nicolás Rincón', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 16:30:00', '2026-11-01 16:30:00'),
  ('d70cade7-766f-50ee-935a-1e8a35deda24', 'daniela.escobar31@ejemplo.test', 'Daniela Escobar', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 16:37:00', '2026-11-01 16:37:00'),
  ('e42cb46f-a779-5157-87f1-a57f56acc71d', 'juan.vega32@ejemplo.test', 'Juan Sebastián Vega', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 16:44:00', '2026-11-01 16:44:00'),
  ('4689cd87-ed8a-5d8c-8d6c-7a657a628efb', 'ximena.puentes33@ejemplo.test', 'Ximena Puentes', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 16:51:00', '2026-11-01 16:51:00'),
  ('10aa85bd-4011-5187-8f1f-334ed61ed85d', 'sergio.aguilar34@ejemplo.test', 'Sergio Aguilar', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 16:58:00', '2026-11-01 16:58:00'),
  ('415bc3de-3e44-5c96-bc64-f3381402cbfb', 'gabriela.pineda35@ejemplo.test', 'Gabriela Pineda', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 17:05:00', '2026-11-01 17:05:00'),
  ('8c180eed-291f-5f50-b0ca-8f9f8827909c', 'esteban.cely36@ejemplo.test', 'Esteban Cely', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 17:12:00', '2026-11-01 17:12:00'),
  ('ddb71344-a258-503e-8c4d-326be3287951', 'lorena.ortiz37@ejemplo.test', 'Lorena Ortiz', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 17:19:00', '2026-11-01 17:19:00'),
  ('073507c2-e147-51e1-9a21-54e054bf7c9d', 'camilo.pardo38@ejemplo.test', 'Camilo Pardo', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 17:26:00', '2026-11-01 17:26:00'),
  ('15062107-f3df-5fcd-805e-84bed0793f64', 'valeria.ferreira39@ejemplo.test', 'Valeria Ferreira', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 17:33:00', '2026-11-01 17:33:00'),
  ('1ed6fc06-53d4-53cd-84ad-6e0683b6e829', 'ricardo.duarte40@ejemplo.test', 'Ricardo Duarte', 'sin-acceso-datos-demo', 'visitante', NULL, 1, 1, '2026-11-01 17:40:00', '2026-11-01 17:40:00')
) AS s (id, correo, nombre, hash_contrasena, rol, empresa_id, activo, correo_verificado, creado_en, actualizado_en)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.correo = s.correo, t.nombre = s.nombre, t.hash_contrasena = s.hash_contrasena, t.rol = s.rol, t.empresa_id = s.empresa_id, t.activo = s.activo, t.correo_verificado = s.correo_verificado, t.creado_en = s.creado_en, t.actualizado_en = s.actualizado_en
WHEN NOT MATCHED THEN INSERT (id, correo, nombre, hash_contrasena, rol, empresa_id, activo, correo_verificado, creado_en, actualizado_en) VALUES (s.id, s.correo, s.nombre, s.hash_contrasena, s.rol, s.empresa_id, s.activo, s.correo_verificado, s.creado_en, s.actualizado_en);
GO

-- factores_mfa: 40
MERGE dbo.factores_mfa AS t
USING (VALUES
  ('55105e1d-d31e-54b2-87dc-01384e4503f9', 'a177e696-49b4-5d09-abde-2d59bd1e7a02', 'correo', NULL, 1, 1, NULL, '2026-11-01 13:07:00'),
  ('8d0f675d-d738-5409-aeb8-15c716f0fc5e', 'd79f291a-472f-50b0-9a29-4459030ba085', 'correo', NULL, 1, 1, NULL, '2026-11-01 13:14:00'),
  ('14832eaf-4076-5e92-bf63-dfb6e3b5ca96', '627b22d8-06a4-578d-a530-6dc2023a9161', 'correo', NULL, 1, 1, NULL, '2026-11-01 13:21:00'),
  ('33b7cd25-0465-54f1-8b33-3b98cae9867f', '7c2e3120-fae3-57a6-a41c-b2ec72fe95be', 'correo', NULL, 1, 1, NULL, '2026-11-01 13:28:00'),
  ('c09146ea-e1f8-59c8-a519-ade3dc6743bb', 'ddd244ae-1f98-5dca-9159-1768a3be5469', 'correo', NULL, 1, 1, NULL, '2026-11-01 13:35:00'),
  ('475254b5-b7ef-52c1-9ae6-7040489b887d', '6563dc18-6925-5bf6-b6b5-c4346f0d0695', 'correo', NULL, 1, 1, NULL, '2026-11-01 13:42:00'),
  ('e8cbe545-6eff-531f-bfb7-1bf2856916e2', '198cce25-3f14-535f-b08e-eda81fe5214b', 'correo', NULL, 1, 1, NULL, '2026-11-01 13:49:00'),
  ('2417f53c-ce68-534e-adb9-2295bd9a9738', 'cd34c792-8f86-5f1b-827c-340492b1cbf9', 'correo', NULL, 1, 1, NULL, '2026-11-01 13:56:00'),
  ('2f5b23e2-e564-56f2-a033-63681ac74589', '832ed401-4b38-5749-a3f6-2ce03953d45d', 'correo', NULL, 1, 1, NULL, '2026-11-01 14:03:00'),
  ('ec34d691-8749-574f-b1a4-4e2f7b4037cc', 'e0dfa9d1-3e16-5daf-9197-bb4a47f04af0', 'correo', NULL, 1, 1, NULL, '2026-11-01 14:10:00'),
  ('bd66ec9a-3854-524d-9270-35af61c1e00e', '09e7aee2-8f6d-5cd1-a53a-ff6794cb96ff', 'correo', NULL, 1, 1, NULL, '2026-11-01 14:17:00'),
  ('b578af9c-9461-5c66-8bb2-2a0a2403daa8', '0644d343-d855-5112-ad4d-72dd22b0316c', 'correo', NULL, 1, 1, NULL, '2026-11-01 14:24:00'),
  ('cd87c9be-ba5c-51ad-9643-fbd00cd17689', 'a778c573-211e-58a2-becd-e58bfbd9155d', 'correo', NULL, 1, 1, NULL, '2026-11-01 14:31:00'),
  ('953349db-ae38-55c7-824c-4ee3d95d38f2', '2aab8617-393a-56ab-aee3-d28e1eb093e6', 'correo', NULL, 1, 1, NULL, '2026-11-01 14:38:00'),
  ('3d679a32-0716-57d9-8436-0461f129e5a9', '26d4c3ee-5017-5c37-b5d5-d8d4de5cf9a9', 'correo', NULL, 1, 1, NULL, '2026-11-01 14:45:00'),
  ('23bc93c0-2c05-5ddf-b175-9f63aba0a2f3', '186532f0-d614-5680-8cfe-4177869fba67', 'correo', NULL, 1, 1, NULL, '2026-11-01 14:52:00'),
  ('08c61a48-0d53-572b-bad6-c77eeb4bb3cf', '67aa2594-cb2e-5801-b731-5cbf8504897e', 'correo', NULL, 1, 1, NULL, '2026-11-01 14:59:00'),
  ('ff4a1777-ec9c-5636-add0-7388492be586', '6fa7aed3-f33b-54fe-82b6-2fd72721bea7', 'correo', NULL, 1, 1, NULL, '2026-11-01 15:06:00'),
  ('9f697b77-c078-5aef-9957-c24b46143b3e', '61770e1d-e345-5165-b7e8-92cbbe0ae957', 'correo', NULL, 1, 1, NULL, '2026-11-01 15:13:00'),
  ('33b69041-e46d-5dfe-8367-6c387938c790', 'e1192882-1157-5928-8f4e-b907cad0c35e', 'correo', NULL, 1, 1, NULL, '2026-11-01 15:20:00'),
  ('bfbc98f0-bddd-5888-a30e-3d2ca38dbb97', '27c894cf-bff3-501a-a842-be2b6b0d7f74', 'correo', NULL, 1, 1, NULL, '2026-11-01 15:27:00'),
  ('f3804bd2-d0fe-5150-8016-c034ac8c407f', '653fa7ab-7f55-5b9d-9362-5627dc133163', 'correo', NULL, 1, 1, NULL, '2026-11-01 15:34:00'),
  ('f2c6c0f1-2330-5114-9a5a-12b93e7dd3ee', '5704d7e2-0919-5356-a2c7-6f6bcc8eda45', 'correo', NULL, 1, 1, NULL, '2026-11-01 15:41:00'),
  ('2a0d5f50-7171-542c-8248-01f19bc3bc26', '49d10a81-ff48-573a-ba6d-a66a60c163b4', 'correo', NULL, 1, 1, NULL, '2026-11-01 15:48:00'),
  ('73bad222-d754-53b6-9980-cba2defedeb3', '4b8d9fff-e783-55b7-a98d-f67706ed6000', 'correo', NULL, 1, 1, NULL, '2026-11-01 15:55:00'),
  ('c46031c1-8fc1-5d57-a033-2fb1e8d97c30', '6088a3bf-51ad-5f13-b835-c3a4c59f74f3', 'correo', NULL, 1, 1, NULL, '2026-11-01 16:02:00'),
  ('643bb896-9766-5bcf-a43c-5339a33fe399', 'a016b6d7-8a58-58a0-96aa-c5d7cb348ffd', 'correo', NULL, 1, 1, NULL, '2026-11-01 16:09:00'),
  ('da85d61a-02db-5521-b251-71ab81992006', 'df886d3c-421b-56eb-a26a-2b5df2cb1e2b', 'correo', NULL, 1, 1, NULL, '2026-11-01 16:16:00'),
  ('ed678dbd-d975-5e84-8988-c55e1f765cdb', '964db46d-079e-53a5-919b-99c3ff407d5c', 'correo', NULL, 1, 1, NULL, '2026-11-01 16:23:00'),
  ('2d3c2fc6-013c-5dda-a0f8-924b8ab7b279', '92bf56c0-70d9-5d1d-adb9-533e0dada1c4', 'correo', NULL, 1, 1, NULL, '2026-11-01 16:30:00'),
  ('d24a1dd1-812f-56c5-88ad-c2d53afd0583', 'd70cade7-766f-50ee-935a-1e8a35deda24', 'correo', NULL, 1, 1, NULL, '2026-11-01 16:37:00'),
  ('306f0bee-a46f-52a2-a36e-a3d9bab76154', 'e42cb46f-a779-5157-87f1-a57f56acc71d', 'correo', NULL, 1, 1, NULL, '2026-11-01 16:44:00'),
  ('2fa9a0e5-f7e2-5634-a5bc-0ce7f8766170', '4689cd87-ed8a-5d8c-8d6c-7a657a628efb', 'correo', NULL, 1, 1, NULL, '2026-11-01 16:51:00'),
  ('a8326693-c269-52f4-88d9-f3ed2586dbf2', '10aa85bd-4011-5187-8f1f-334ed61ed85d', 'correo', NULL, 1, 1, NULL, '2026-11-01 16:58:00'),
  ('6994cd72-f4c5-506c-b460-1fcd9a42e1f8', '415bc3de-3e44-5c96-bc64-f3381402cbfb', 'correo', NULL, 1, 1, NULL, '2026-11-01 17:05:00'),
  ('89671246-fc40-57f3-a638-48ec900f181a', '8c180eed-291f-5f50-b0ca-8f9f8827909c', 'correo', NULL, 1, 1, NULL, '2026-11-01 17:12:00'),
  ('a3f135ec-0aaa-5a36-b233-58568d9dbdf8', 'ddb71344-a258-503e-8c4d-326be3287951', 'correo', NULL, 1, 1, NULL, '2026-11-01 17:19:00'),
  ('a86b098f-9a91-5ad6-990b-cfd5b3d77c00', '073507c2-e147-51e1-9a21-54e054bf7c9d', 'correo', NULL, 1, 1, NULL, '2026-11-01 17:26:00'),
  ('377fc189-d7c5-5927-8796-0c929a8bcf56', '15062107-f3df-5fcd-805e-84bed0793f64', 'correo', NULL, 1, 1, NULL, '2026-11-01 17:33:00'),
  ('a6cc04e8-95c2-5144-8e7e-01997e2cc4b2', '1ed6fc06-53d4-53cd-84ad-6e0683b6e829', 'correo', NULL, 1, 1, NULL, '2026-11-01 17:40:00')
) AS s (id, usuario_id, tipo, secreto_cifrado, activo, preferido, ultimo_paso, creado_en)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.usuario_id = s.usuario_id, t.tipo = s.tipo, t.secreto_cifrado = s.secreto_cifrado, t.activo = s.activo, t.preferido = s.preferido, t.ultimo_paso = s.ultimo_paso, t.creado_en = s.creado_en
WHEN NOT MATCHED THEN INSERT (id, usuario_id, tipo, secreto_cifrado, activo, preferido, ultimo_paso, creado_en) VALUES (s.id, s.usuario_id, s.tipo, s.secreto_cifrado, s.activo, s.preferido, s.ultimo_paso, s.creado_en);
GO

-- eventos: 3
MERGE dbo.eventos AS t
USING (VALUES
  ('d4436d99-db9d-57eb-a07d-f133467a819b', 'ExpoNexo Innovación 2026', 'exponexo-innovacion-2026', 'Feria de innovación, tecnología y negocios.', '2026-11-24 14:00:00', '2026-11-27 23:00:00', 'publicado', 85000.00, 5000, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('18fb431a-7d31-5ee7-ae16-402f2199bcd5', 'ExpoNexo Manufactura 2027', 'exponexo-manufactura-2027', 'Manufactura, automatización e industria 4.0.', '2027-03-09 14:00:00', '2027-03-12 23:00:00', 'publicado', 120000.00, 4000, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('0dbd55eb-2a5b-5a43-8016-9a919efbbd32', 'ExpoNexo Agroindustria 2027', 'exponexo-agroindustria-2027', 'Agroindustria, sostenibilidad y cadena de suministro.', '2027-06-15 14:00:00', '2027-06-18 23:00:00', 'borrador', 95000.00, 3000, '2026-11-01 13:00:00', '2026-11-01 13:00:00')
) AS s (id, nombre, slug, descripcion, inicio, fin, estado, precio_entrada, aforo, creado_en, actualizado_en)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.nombre = s.nombre, t.slug = s.slug, t.descripcion = s.descripcion, t.inicio = s.inicio, t.fin = s.fin, t.estado = s.estado, t.precio_entrada = s.precio_entrada, t.aforo = s.aforo, t.creado_en = s.creado_en, t.actualizado_en = s.actualizado_en
WHEN NOT MATCHED THEN INSERT (id, nombre, slug, descripcion, inicio, fin, estado, precio_entrada, aforo, creado_en, actualizado_en) VALUES (s.id, s.nombre, s.slug, s.descripcion, s.inicio, s.fin, s.estado, s.precio_entrada, s.aforo, s.creado_en, s.actualizado_en);
GO

-- pabellones: 4
MERGE dbo.pabellones AS t
USING (VALUES
  ('090dc046-228c-52cd-9acc-0197ff57bf0d', 'Pabellón Norte', 12, NULL, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'Pabellón Sur', 12, NULL, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('40b2f325-9319-5cdf-b292-f691b55e7398', 'Pabellón Oriente', 12, NULL, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'Pabellón Occidente', 12, NULL, '2026-11-01 13:00:00', '2026-11-01 13:00:00')
) AS s (id, nombre, capacidad_stands, plano_url, creado_en, actualizado_en)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.nombre = s.nombre, t.capacidad_stands = s.capacidad_stands, t.plano_url = s.plano_url, t.creado_en = s.creado_en, t.actualizado_en = s.actualizado_en
WHEN NOT MATCHED THEN INSERT (id, nombre, capacidad_stands, plano_url, creado_en, actualizado_en) VALUES (s.id, s.nombre, s.capacidad_stands, s.plano_url, s.creado_en, s.actualizado_en);
GO

-- stands: 48
MERGE dbo.stands AS t
USING (VALUES
  ('cac48c42-c222-5027-890e-30b126f56d76', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-101', 12.00, 'esquinero', 3200000.00, 1, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('78eadce6-b873-54fc-8200-7935561e4277', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-102', 9.00, 'basico', 2500000.00, 1, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('92fb325a-2b83-5dd7-b2f7-d90376a5cfa0', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-103', 9.00, 'basico', 2500000.00, 1, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('626dc4ab-2929-5b95-807f-bb39e48417e8', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-104', 12.00, 'esquinero', 3200000.00, 1, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('4e7220fe-f3a7-5cb8-95a8-f42d62eba1d9', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-201', 9.00, 'basico', 2500000.00, 2, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('095f725d-76a7-5e28-8a85-b5217802a582', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-202', 18.00, 'isla', 4800000.00, 2, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('8812649d-ce90-5dce-ac13-095f17b8bb0d', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-203', 18.00, 'isla', 4800000.00, 2, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('5c2f80d1-12cb-53af-ba46-584e846b6095', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-204', 9.00, 'basico', 2500000.00, 2, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('ef4abec7-3146-51fd-adac-1d069a55c38d', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-301', 12.00, 'esquinero', 3200000.00, 3, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('65f1e7af-7c0e-5ed2-8f36-79747682fafa', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-302', 9.00, 'basico', 2500000.00, 3, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('7ba1778e-08cc-5c06-97a7-9d99e354bf5b', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-303', 9.00, 'basico', 2500000.00, 3, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('ebb479d4-3ee6-5b9a-8c20-c9bf7c9bd682', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'N-304', 12.00, 'esquinero', 3200000.00, 3, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('ab72326c-6c50-5814-bb3c-e7c3fa002f63', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-101', 12.00, 'esquinero', 3200000.00, 1, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('9e88ce5b-0a97-58bc-aa48-2ee0c150a52f', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-102', 9.00, 'basico', 2500000.00, 1, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('ed6f32fa-6e35-5ca2-bafd-0edea263b2ef', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-103', 9.00, 'basico', 2500000.00, 1, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('43f4f308-3853-5eb5-ae99-4e073e5643bb', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-104', 12.00, 'esquinero', 3200000.00, 1, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('f399d331-7ea6-5332-9335-b0fcf0cbf367', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-201', 9.00, 'basico', 2500000.00, 2, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('d7a0446e-06e9-5689-a61f-9ec098b2fec5', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-202', 18.00, 'isla', 4800000.00, 2, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('4f566d86-81d8-5824-a079-fd5fe293af9e', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-203', 18.00, 'isla', 4800000.00, 2, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('d2aebb90-24fc-5320-bbe7-d95cfa18dadc', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-204', 9.00, 'basico', 2500000.00, 2, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('313bc462-8dac-594c-95b4-88b0684558c6', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-301', 12.00, 'esquinero', 3200000.00, 3, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('ecd59400-7551-5a0c-9712-2d072492b9ad', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-302', 9.00, 'basico', 2500000.00, 3, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('0312808b-123a-5937-856e-e90cc17ac1df', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-303', 9.00, 'basico', 2500000.00, 3, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('268e16f4-ac97-561e-b476-35970ccf5850', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'S-304', 12.00, 'esquinero', 3200000.00, 3, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('6b8236ac-9d88-5107-b6b3-00c21ebd9e39', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-101', 12.00, 'esquinero', 3200000.00, 1, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('58b6d8d4-75dc-58ed-8067-79a018486149', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-102', 9.00, 'basico', 2500000.00, 1, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('287766e2-4119-50c9-b89c-bbc8b451f066', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-103', 9.00, 'basico', 2500000.00, 1, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('2b40dd50-614e-584a-b830-488f12b445cb', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-104', 12.00, 'esquinero', 3200000.00, 1, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('1cdd5bc7-cca9-544d-b4bc-e5e1b6073b8e', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-201', 9.00, 'basico', 2500000.00, 2, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('15725997-1a64-540f-a8e0-1b3e60c8efdf', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-202', 18.00, 'isla', 4800000.00, 2, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('aa1ad6ed-2540-5ee2-bf1d-bc7fdde6f0a0', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-203', 18.00, 'isla', 4800000.00, 2, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('40db1843-618b-57fa-878a-e795d3584a4d', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-204', 9.00, 'basico', 2500000.00, 2, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('a5a450b7-90a0-5f27-a317-5e7329a7a4e8', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-301', 12.00, 'esquinero', 3200000.00, 3, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('a01b03d6-4f29-5462-a94a-fd1c4dfb635a', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-302', 9.00, 'basico', 2500000.00, 3, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('0126c84d-40d9-5979-b2a8-ded71d4d8576', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-303', 9.00, 'basico', 2500000.00, 3, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('8445d401-f6f9-5b3b-82cc-52111d9726d4', '40b2f325-9319-5cdf-b292-f691b55e7398', 'O-304', 12.00, 'esquinero', 3200000.00, 3, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('5811f207-c5a4-547e-b29c-e5439320d883', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-101', 12.00, 'esquinero', 3200000.00, 1, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('6d24f4b1-cd00-52e0-88df-543cb38becae', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-102', 9.00, 'basico', 2500000.00, 1, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('3cd6b14a-9457-507f-a3b7-0b1c8ed841d8', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-103', 9.00, 'basico', 2500000.00, 1, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('764c0eb8-a19a-569b-a150-27a23a86e3d4', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-104', 12.00, 'esquinero', 3200000.00, 1, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('e1076c56-4303-50ca-bbc7-c63ee449d758', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-201', 9.00, 'basico', 2500000.00, 2, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('5f9d85bc-7be4-5c51-9c3f-7c014ebe7c4a', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-202', 18.00, 'isla', 4800000.00, 2, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('40420cc0-bb39-5405-a99e-f088d3d78df2', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-203', 18.00, 'isla', 4800000.00, 2, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('7f066b97-c1df-53c8-a668-57561bcb8183', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-204', 9.00, 'basico', 2500000.00, 2, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('1492ed27-0167-53ee-9a21-2c09bed8f95c', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-301', 12.00, 'esquinero', 3200000.00, 3, 1, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('60420360-3608-5474-a4f4-3250fcbbb434', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-302', 9.00, 'basico', 2500000.00, 3, 2, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('5ccea658-cb21-5b36-88bd-c257a2089081', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-303', 9.00, 'basico', 2500000.00, 3, 3, '2026-11-01 13:00:00', '2026-11-01 13:00:00'),
  ('ec949bba-48d8-5cc9-bea8-f612bf7d231d', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'C-304', 12.00, 'esquinero', 3200000.00, 3, 4, '2026-11-01 13:00:00', '2026-11-01 13:00:00')
) AS s (id, pabellon_id, codigo, metros_cuadrados, tipo, precio_base, fila, columna, creado_en, actualizado_en)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.pabellon_id = s.pabellon_id, t.codigo = s.codigo, t.metros_cuadrados = s.metros_cuadrados, t.tipo = s.tipo, t.precio_base = s.precio_base, t.fila = s.fila, t.columna = s.columna, t.creado_en = s.creado_en, t.actualizado_en = s.actualizado_en
WHEN NOT MATCHED THEN INSERT (id, pabellon_id, codigo, metros_cuadrados, tipo, precio_base, fila, columna, creado_en, actualizado_en) VALUES (s.id, s.pabellon_id, s.codigo, s.metros_cuadrados, s.tipo, s.precio_base, s.fila, s.columna, s.creado_en, s.actualizado_en);
GO

-- salas: 8
MERGE dbo.salas AS t
USING (VALUES
  ('f80e3eca-1ba7-51f5-a57c-562577edac54', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'SALA-N1', 6),
  ('a279fadc-96f3-5766-a697-0dd0be5e02a5', '090dc046-228c-52cd-9acc-0197ff57bf0d', 'SALA-N2', 8),
  ('710c3d78-9972-5f7e-99b1-71827c91098d', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'SALA-S1', 6),
  ('ba0d80c2-65f6-5864-9fd4-50fba13aabe2', 'f1eec2d6-d0c4-5d2d-9802-892b6b824b3b', 'SALA-S2', 8),
  ('92ee0c3f-31d3-5fb9-8053-05837dafcc20', '40b2f325-9319-5cdf-b292-f691b55e7398', 'SALA-O1', 6),
  ('f1a91078-400b-5bf0-ab30-bea030842de0', '40b2f325-9319-5cdf-b292-f691b55e7398', 'SALA-O2', 8),
  ('1ee12ecd-8c42-53b2-af3e-dd185b4f543a', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'SALA-C1', 6),
  ('7a1a57f8-9351-513b-a9ed-b9714cfccd4f', '1a8f025c-04aa-5ae1-a150-9a028dafaabc', 'SALA-C2', 8)
) AS s (id, pabellon_id, codigo, capacidad)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.pabellon_id = s.pabellon_id, t.codigo = s.codigo, t.capacidad = s.capacidad
WHEN NOT MATCHED THEN INSERT (id, pabellon_id, codigo, capacidad) VALUES (s.id, s.pabellon_id, s.codigo, s.capacidad);
GO

-- reservas_stand: 25
MERGE dbo.reservas_stand AS t
USING (VALUES
  ('80b835fa-8448-51b6-8b6f-593b206a4c7c', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'cac48c42-c222-5027-890e-30b126f56d76', '415a4da4-15b5-578b-880d-393afbf9ad5d', 'a177e696-49b4-5d09-abde-2d59bd1e7a02', 'pagada', 3200000.00, '2026-11-01 14:30:00', 'b9ec423b-e80f-5615-833c-2483fa3ba02a', 'demo-reserva-001', 1, '2026-11-01 14:00:00', '2026-11-01 14:00:00'),
  ('20ecdb70-31a8-539d-8b81-84d2f2e4a67b', 'd4436d99-db9d-57eb-a07d-f133467a819b', '92fb325a-2b83-5dd7-b2f7-d90376a5cfa0', '8aef2e0a-6ab9-5915-84f7-b50888b27ba2', 'd79f291a-472f-50b0-9a29-4459030ba085', 'pagada', 2500000.00, '2026-11-01 15:30:00', '024f797b-4aad-5a22-b00c-aa2c87b3247a', 'demo-reserva-002', 1, '2026-11-01 15:00:00', '2026-11-01 15:00:00'),
  ('327c00a1-8fff-530f-813b-78b18d235481', 'd4436d99-db9d-57eb-a07d-f133467a819b', '4e7220fe-f3a7-5cb8-95a8-f42d62eba1d9', '21549906-47ab-55d0-a72a-4ad669f5e8c3', '627b22d8-06a4-578d-a530-6dc2023a9161', 'pagada', 2500000.00, '2026-11-01 16:30:00', 'c5bbb357-c46e-54a2-9787-94267bc2ce2a', 'demo-reserva-003', 1, '2026-11-01 16:00:00', '2026-11-01 16:00:00'),
  ('bef3b283-fdd7-5a3a-a986-137185968bf9', 'd4436d99-db9d-57eb-a07d-f133467a819b', '8812649d-ce90-5dce-ac13-095f17b8bb0d', '13cf73b3-1171-59d1-bb55-815d9c55ce34', '7c2e3120-fae3-57a6-a41c-b2ec72fe95be', 'pagada', 4800000.00, '2026-11-01 17:30:00', 'd5405964-995b-596c-b1d3-fd9642440a66', 'demo-reserva-004', 1, '2026-11-01 17:00:00', '2026-11-01 17:00:00'),
  ('7559bbdd-118b-5988-bd85-b2901dceadbf', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'ef4abec7-3146-51fd-adac-1d069a55c38d', '5e8886b4-f066-556b-bf3b-57d6d5f48521', 'ddd244ae-1f98-5dca-9159-1768a3be5469', 'pagada', 3200000.00, '2026-11-01 18:30:00', '0e86c872-7dee-5a41-9ce5-8e66e5904dc2', 'demo-reserva-005', 1, '2026-11-01 18:00:00', '2026-11-01 18:00:00'),
  ('10a9d8e7-771b-5a82-9d63-0e2a00710e4d', 'd4436d99-db9d-57eb-a07d-f133467a819b', '7ba1778e-08cc-5c06-97a7-9d99e354bf5b', 'c5033e3f-13c3-5f62-9999-a303568b0800', '6563dc18-6925-5bf6-b6b5-c4346f0d0695', 'pagada', 2500000.00, '2026-11-01 19:30:00', 'ad502b82-de2b-5ba4-892c-422d13d4d4a6', 'demo-reserva-006', 1, '2026-11-01 19:00:00', '2026-11-01 19:00:00'),
  ('408b3090-ab5e-584f-8cc6-42ad87293cd4', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'ab72326c-6c50-5814-bb3c-e7c3fa002f63', 'fd37774d-e7d9-5b26-a856-e9513714a8fa', '198cce25-3f14-535f-b08e-eda81fe5214b', 'pagada', 3200000.00, '2026-11-01 20:30:00', '993e52af-36b6-5bae-9ccc-c84206d7ac7d', 'demo-reserva-007', 1, '2026-11-01 20:00:00', '2026-11-01 20:00:00'),
  ('f349fe26-1181-543d-9ba4-5bcb5c7f4cd3', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'ed6f32fa-6e35-5ca2-bafd-0edea263b2ef', '483b6650-695d-500d-9d0b-958eda5d01ea', 'cd34c792-8f86-5f1b-827c-340492b1cbf9', 'pagada', 2500000.00, '2026-11-01 21:30:00', '28d36a42-623a-5eb6-befb-d454bb2eb42f', 'demo-reserva-008', 1, '2026-11-01 21:00:00', '2026-11-01 21:00:00'),
  ('7f96eadb-f4dd-545e-94a6-7ea4ba72596b', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'f399d331-7ea6-5332-9335-b0fcf0cbf367', '077e07aa-674d-581c-abc5-66c53a150952', '832ed401-4b38-5749-a3f6-2ce03953d45d', 'pagada', 2500000.00, '2026-11-01 22:30:00', '23145c9a-87b6-54c0-adbd-d108a4976398', 'demo-reserva-009', 1, '2026-11-01 22:00:00', '2026-11-01 22:00:00'),
  ('ac8f8aad-c9f1-5dc8-91b0-9e8df8b38457', 'd4436d99-db9d-57eb-a07d-f133467a819b', '4f566d86-81d8-5824-a079-fd5fe293af9e', '355cb4e6-7cff-5c0d-8893-6d7d339b7368', 'e0dfa9d1-3e16-5daf-9197-bb4a47f04af0', 'pagada', 4800000.00, '2026-11-01 23:30:00', '72fb84f3-5d51-596b-857d-6a9eba00fc73', 'demo-reserva-010', 1, '2026-11-01 23:00:00', '2026-11-01 23:00:00'),
  ('4b14247c-9c8b-5269-bcc2-8dc9ba883d76', 'd4436d99-db9d-57eb-a07d-f133467a819b', '313bc462-8dac-594c-95b4-88b0684558c6', 'b79937d6-a7ec-5897-812f-761f91254b2f', '09e7aee2-8f6d-5cd1-a53a-ff6794cb96ff', 'pagada', 3200000.00, '2026-11-02 00:30:00', '0bdde4c8-2cd2-58dc-945e-8291ab2c3257', 'demo-reserva-011', 1, '2026-11-02 00:00:00', '2026-11-02 00:00:00'),
  ('3f03224e-b298-5c0a-a17e-33bd01a3b5d3', 'd4436d99-db9d-57eb-a07d-f133467a819b', '0312808b-123a-5937-856e-e90cc17ac1df', 'a5ecfb5d-0671-5bb6-a5e1-5c227c7f9ecd', '0644d343-d855-5112-ad4d-72dd22b0316c', 'pagada', 2500000.00, '2026-11-02 01:30:00', 'd48ea896-665a-5f31-983d-6f5d488ff463', 'demo-reserva-012', 1, '2026-11-02 01:00:00', '2026-11-02 01:00:00'),
  ('ec833d22-f333-5b57-8dc4-094a24e730dd', 'd4436d99-db9d-57eb-a07d-f133467a819b', '6b8236ac-9d88-5107-b6b3-00c21ebd9e39', '2f59ba7e-cc6d-5c00-9d36-1c06b57f690a', 'a778c573-211e-58a2-becd-e58bfbd9155d', 'pendiente_pago', 3200000.00, '2026-11-02 02:30:00', NULL, 'demo-reserva-013', 1, '2026-11-02 02:00:00', '2026-11-02 02:00:00'),
  ('d1e55365-6d42-5091-ab4f-3246ae405d9a', 'd4436d99-db9d-57eb-a07d-f133467a819b', '287766e2-4119-50c9-b89c-bbc8b451f066', '0799143f-ebe6-5395-8d69-2837276f7c49', '2aab8617-393a-56ab-aee3-d28e1eb093e6', 'pendiente_pago', 2500000.00, '2026-11-02 03:30:00', 'a0f50412-70ad-5702-803e-e315402a1afd', 'demo-reserva-014', 1, '2026-11-02 03:00:00', '2026-11-02 03:00:00'),
  ('a80f207f-2277-5e4a-90ab-d3c1e85e5db5', 'd4436d99-db9d-57eb-a07d-f133467a819b', '1cdd5bc7-cca9-544d-b4bc-e5e1b6073b8e', '5e4eec28-eeb8-58e9-bc1b-31f6f886acd0', '26d4c3ee-5017-5c37-b5d5-d8d4de5cf9a9', 'pendiente_pago', 2500000.00, '2026-11-02 04:30:00', NULL, 'demo-reserva-015', 1, '2026-11-02 04:00:00', '2026-11-02 04:00:00'),
  ('11cd2346-78af-5e67-b055-7b56c1cd42b9', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '78eadce6-b873-54fc-8200-7935561e4277', '415a4da4-15b5-578b-880d-393afbf9ad5d', 'a177e696-49b4-5d09-abde-2d59bd1e7a02', 'pendiente_pago', 2500000.00, '2026-11-02 05:30:00', '5edebd10-455b-525a-959b-43739a7580f9', 'demo-reserva-016', 1, '2026-11-02 05:00:00', '2026-11-02 05:00:00'),
  ('4e074ece-db53-5078-98ea-102aa62a8a41', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '095f725d-76a7-5e28-8a85-b5217802a582', '8aef2e0a-6ab9-5915-84f7-b50888b27ba2', 'd79f291a-472f-50b0-9a29-4459030ba085', 'pendiente_pago', 4800000.00, '2026-11-02 06:30:00', NULL, 'demo-reserva-017', 1, '2026-11-02 06:00:00', '2026-11-02 06:00:00'),
  ('cd198e20-2ad9-53de-815b-d69c37126dca', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '65f1e7af-7c0e-5ed2-8f36-79747682fafa', '21549906-47ab-55d0-a72a-4ad669f5e8c3', '627b22d8-06a4-578d-a530-6dc2023a9161', 'pendiente_pago', 2500000.00, '2026-11-02 07:30:00', 'e7dbddb2-4c8b-5274-a624-060b8ecd3611', 'demo-reserva-018', 1, '2026-11-02 07:00:00', '2026-11-02 07:00:00'),
  ('684c3683-d253-5c3c-9859-119f61d65f36', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '9e88ce5b-0a97-58bc-aa48-2ee0c150a52f', '13cf73b3-1171-59d1-bb55-815d9c55ce34', '7c2e3120-fae3-57a6-a41c-b2ec72fe95be', 'pendiente_pago', 2500000.00, '2026-11-02 08:30:00', NULL, 'demo-reserva-019', 1, '2026-11-02 08:00:00', '2026-11-02 08:00:00'),
  ('3b3840b0-842c-556c-8326-0e2b8a30995c', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', 'd7a0446e-06e9-5689-a61f-9ec098b2fec5', '5e8886b4-f066-556b-bf3b-57d6d5f48521', 'ddd244ae-1f98-5dca-9159-1768a3be5469', 'cancelada', 4800000.00, '2026-11-02 09:30:00', '97eb1f62-45a9-5f8a-b31f-4916c7d5dab9', 'demo-reserva-020', 1, '2026-11-02 09:00:00', '2026-11-02 09:00:00'),
  ('2ff7cdc2-e38a-50bf-89cc-1193779144ef', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', 'ecd59400-7551-5a0c-9712-2d072492b9ad', 'c5033e3f-13c3-5f62-9999-a303568b0800', '6563dc18-6925-5bf6-b6b5-c4346f0d0695', 'cancelada', 2500000.00, '2026-11-02 10:30:00', NULL, 'demo-reserva-021', 1, '2026-11-02 10:00:00', '2026-11-02 10:00:00'),
  ('c6db271f-9c15-5102-9db6-9e2ef9e4fb35', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '58b6d8d4-75dc-58ed-8067-79a018486149', 'fd37774d-e7d9-5b26-a856-e9513714a8fa', '198cce25-3f14-535f-b08e-eda81fe5214b', 'cancelada', 2500000.00, '2026-11-02 11:30:00', NULL, 'demo-reserva-022', 1, '2026-11-02 11:00:00', '2026-11-02 11:00:00'),
  ('c8374703-6b65-5c99-9b16-86432a1ede8d', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '15725997-1a64-540f-a8e0-1b3e60c8efdf', '483b6650-695d-500d-9d0b-958eda5d01ea', 'cd34c792-8f86-5f1b-827c-340492b1cbf9', 'cancelada', 4800000.00, '2026-11-02 12:30:00', NULL, 'demo-reserva-023', 1, '2026-11-02 12:00:00', '2026-11-02 12:00:00'),
  ('e6b6ca49-49fc-5362-8777-52c0f3ce7a14', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', 'a01b03d6-4f29-5462-a94a-fd1c4dfb635a', '077e07aa-674d-581c-abc5-66c53a150952', '832ed401-4b38-5749-a3f6-2ce03953d45d', 'vencida', 2500000.00, '2026-11-02 13:30:00', 'fa8c612c-d4da-5d39-ab04-5c71b475a279', 'demo-reserva-024', 1, '2026-11-02 13:00:00', '2026-11-02 13:00:00'),
  ('e3d1c6c6-f0be-50e9-9246-4aff3380e801', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '6d24f4b1-cd00-52e0-88df-543cb38becae', '355cb4e6-7cff-5c0d-8893-6d7d339b7368', 'e0dfa9d1-3e16-5daf-9197-bb4a47f04af0', 'vencida', 2500000.00, '2026-11-02 14:30:00', 'd95e0306-0a30-557b-852f-f040ac2558f5', 'demo-reserva-025', 1, '2026-11-02 14:00:00', '2026-11-02 14:00:00')
) AS s (id, evento_id, stand_id, empresa_id, usuario_id, estado, monto, vence_en, orden_pago_id, clave_idempotencia, version, creado_en, actualizado_en)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.evento_id = s.evento_id, t.stand_id = s.stand_id, t.empresa_id = s.empresa_id, t.usuario_id = s.usuario_id, t.estado = s.estado, t.monto = s.monto, t.vence_en = s.vence_en, t.orden_pago_id = s.orden_pago_id, t.clave_idempotencia = s.clave_idempotencia, t.version = s.version, t.creado_en = s.creado_en, t.actualizado_en = s.actualizado_en
WHEN NOT MATCHED THEN INSERT (id, evento_id, stand_id, empresa_id, usuario_id, estado, monto, vence_en, orden_pago_id, clave_idempotencia, version, creado_en, actualizado_en) VALUES (s.id, s.evento_id, s.stand_id, s.empresa_id, s.usuario_id, s.estado, s.monto, s.vence_en, s.orden_pago_id, s.clave_idempotencia, s.version, s.creado_en, s.actualizado_en);
GO

-- entradas: 40
MERGE dbo.entradas AS t
USING (VALUES
  ('a072fd40-03ca-57a0-b080-989b4bdda62c', 'd4436d99-db9d-57eb-a07d-f133467a819b', '186532f0-d614-5680-8cfe-4177869fba67', 'general', 'activa', 'e342132f-a3e1-5028-a3a0-4f4b580f0c3b', 'demo-qr-001', NULL, NULL, '2026-11-02 13:11:00'),
  ('5c74a02f-63be-573d-aab7-a300f344289d', 'd4436d99-db9d-57eb-a07d-f133467a819b', '67aa2594-cb2e-5801-b731-5cbf8504897e', 'general', 'activa', '05a447e9-4279-5a37-b0e1-9c0577acb808', 'demo-qr-002', NULL, NULL, '2026-11-02 13:22:00'),
  ('dabab8a8-ec6a-5e2a-ac4a-e54ad0ef811b', 'd4436d99-db9d-57eb-a07d-f133467a819b', '6fa7aed3-f33b-54fe-82b6-2fd72721bea7', 'negocios', 'activa', '1fbbe64e-07d4-5926-a62d-60e980d41aaf', 'demo-qr-003', NULL, NULL, '2026-11-02 13:33:00'),
  ('54855305-8829-5d8e-8442-27054fb4ba83', 'd4436d99-db9d-57eb-a07d-f133467a819b', '61770e1d-e345-5165-b7e8-92cbbe0ae957', 'general', 'activa', '6167cdc6-1632-5c6d-884a-61886fffc403', 'demo-qr-004', NULL, NULL, '2026-11-02 13:44:00'),
  ('f279487b-2726-59a7-871e-ce2e63543a63', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'e1192882-1157-5928-8f4e-b907cad0c35e', 'prensa', 'activa', '095f8fc4-fd24-5b73-8bc7-ead921beff74', 'demo-qr-005', NULL, NULL, '2026-11-02 13:55:00'),
  ('2dd3a42d-90bf-5ce3-8291-21b2db7d68e9', 'd4436d99-db9d-57eb-a07d-f133467a819b', '27c894cf-bff3-501a-a842-be2b6b0d7f74', 'general', 'activa', '2a36c8e2-fb57-589b-a04c-d08dd2496565', 'demo-qr-006', NULL, NULL, '2026-11-02 14:06:00'),
  ('d165aa96-3373-5d83-ab14-5bd502e13d63', 'd4436d99-db9d-57eb-a07d-f133467a819b', '653fa7ab-7f55-5b9d-9362-5627dc133163', 'general', 'activa', 'a7160abd-6984-52a7-96b0-28b2cd1d0486', 'demo-qr-007', NULL, NULL, '2026-11-02 14:17:00'),
  ('16bb5914-37dd-599d-81f5-d0d3343159bc', 'd4436d99-db9d-57eb-a07d-f133467a819b', '5704d7e2-0919-5356-a2c7-6f6bcc8eda45', 'negocios', 'activa', 'fb222546-ece4-56b7-ac49-409ef38b4298', 'demo-qr-008', NULL, NULL, '2026-11-02 14:28:00'),
  ('7c3d0c49-9739-5d17-85a6-11df9b3d0074', 'd4436d99-db9d-57eb-a07d-f133467a819b', '49d10a81-ff48-573a-ba6d-a66a60c163b4', 'general', 'activa', 'c14ef7ae-239d-54b6-9a40-3212c55e4a84', 'demo-qr-009', NULL, NULL, '2026-11-02 14:39:00'),
  ('dd6608f7-5b0c-5ed2-9e16-01548c743e95', 'd4436d99-db9d-57eb-a07d-f133467a819b', '4b8d9fff-e783-55b7-a98d-f67706ed6000', 'prensa', 'usada', 'a80ce959-1d95-54ec-9b66-bf0d081ffe35', 'demo-qr-010', '2026-11-24 15:50:00', 'TRN-01', '2026-11-02 14:50:00'),
  ('c53eccc1-92e7-564d-bdd8-7b250b1ddc45', 'd4436d99-db9d-57eb-a07d-f133467a819b', '6088a3bf-51ad-5f13-b835-c3a4c59f74f3', 'general', 'usada', '67a19202-dc8a-5124-b634-31423c5bc140', 'demo-qr-011', '2026-11-24 15:55:00', 'TRN-01', '2026-11-02 15:01:00'),
  ('737003fb-4401-55e2-95ad-bcf948bd1c55', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'a016b6d7-8a58-58a0-96aa-c5d7cb348ffd', 'general', 'usada', '7ffc6f2a-53bc-5590-8a91-f35651919f44', 'demo-qr-012', '2026-11-24 16:00:00', 'TRN-01', '2026-11-02 15:12:00'),
  ('1c095e82-c54e-5382-94e7-2171f3ee7df4', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'df886d3c-421b-56eb-a26a-2b5df2cb1e2b', 'negocios', 'usada', '0af366cc-4db8-553f-b7b9-b93963dbe8c1', 'demo-qr-013', '2026-11-24 16:05:00', 'TRN-01', '2026-11-02 15:23:00'),
  ('9c3d0b8a-5368-541b-8dc6-9f3eb88b2fba', 'd4436d99-db9d-57eb-a07d-f133467a819b', '964db46d-079e-53a5-919b-99c3ff407d5c', 'general', 'usada', '276ed590-d604-59be-974c-69485cd21336', 'demo-qr-014', '2026-11-24 16:10:00', 'TRN-01', '2026-11-02 15:34:00'),
  ('db043b5a-56c0-5e60-8697-5cfeccedca40', 'd4436d99-db9d-57eb-a07d-f133467a819b', '92bf56c0-70d9-5d1d-adb9-533e0dada1c4', 'prensa', 'usada', '0c2e9695-ed54-5456-a402-f16521e6274e', 'demo-qr-015', '2026-11-24 16:15:00', 'TRN-01', '2026-11-02 15:45:00'),
  ('3e9ca681-b08e-535b-a774-88d653a445f3', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'd70cade7-766f-50ee-935a-1e8a35deda24', 'general', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 15:56:00'),
  ('bee08488-ee65-505d-bc16-e30efa6af2a2', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'e42cb46f-a779-5157-87f1-a57f56acc71d', 'general', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 16:07:00'),
  ('4b59385d-88be-5de2-84e1-985f0d432106', 'd4436d99-db9d-57eb-a07d-f133467a819b', '4689cd87-ed8a-5d8c-8d6c-7a657a628efb', 'negocios', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 16:18:00'),
  ('d8d44ed6-7765-5181-a72a-8c3114824e43', 'd4436d99-db9d-57eb-a07d-f133467a819b', '10aa85bd-4011-5187-8f1f-334ed61ed85d', 'general', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 16:29:00'),
  ('e2e3a1e7-0c74-5fe8-98f1-56226b29dc96', 'd4436d99-db9d-57eb-a07d-f133467a819b', '415bc3de-3e44-5c96-bc64-f3381402cbfb', 'prensa', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 16:40:00'),
  ('6862571e-b159-568a-b68f-58691b96b73d', 'd4436d99-db9d-57eb-a07d-f133467a819b', '8c180eed-291f-5f50-b0ca-8f9f8827909c', 'general', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 16:51:00'),
  ('f05beb90-1e17-525a-9d7e-df5faae41922', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'ddb71344-a258-503e-8c4d-326be3287951', 'general', 'cancelada', NULL, NULL, NULL, NULL, '2026-11-02 17:02:00'),
  ('a8a315d4-cce6-5441-a162-fcf639934407', 'd4436d99-db9d-57eb-a07d-f133467a819b', '073507c2-e147-51e1-9a21-54e054bf7c9d', 'negocios', 'cancelada', NULL, NULL, NULL, NULL, '2026-11-02 17:13:00'),
  ('fc7f1854-2341-56cf-bfbe-1a6128dc0d20', 'd4436d99-db9d-57eb-a07d-f133467a819b', '15062107-f3df-5fcd-805e-84bed0793f64', 'general', 'cancelada', NULL, NULL, NULL, NULL, '2026-11-02 17:24:00'),
  ('49b6ded1-4c4f-5068-af68-5b9a20994e41', 'd4436d99-db9d-57eb-a07d-f133467a819b', '1ed6fc06-53d4-53cd-84ad-6e0683b6e829', 'prensa', 'cancelada', NULL, NULL, NULL, NULL, '2026-11-02 17:35:00'),
  ('e8b7f108-2d1f-5e50-bbe9-a48e111db6ad', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '186532f0-d614-5680-8cfe-4177869fba67', 'general', 'activa', 'a603793c-c53c-533e-b399-b6b01b12055d', 'demo-qr-026', NULL, NULL, '2026-11-02 17:46:00'),
  ('35e682ce-bb28-5fbb-90fe-4b24b962f4e6', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '67aa2594-cb2e-5801-b731-5cbf8504897e', 'general', 'activa', 'b9d9ba9d-c4dd-5ffc-af0e-fcc6964ef00a', 'demo-qr-027', NULL, NULL, '2026-11-02 17:57:00'),
  ('c070094d-5cc3-5fb7-baac-892abf9eaadc', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '6fa7aed3-f33b-54fe-82b6-2fd72721bea7', 'negocios', 'activa', '7e2e5b62-5e38-5457-9c9b-cfe8ac546cde', 'demo-qr-028', NULL, NULL, '2026-11-02 18:08:00'),
  ('b22f91eb-3c01-5228-bcb0-186b5c50a382', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '61770e1d-e345-5165-b7e8-92cbbe0ae957', 'general', 'activa', 'da696912-4395-586b-834d-126d2fada610', 'demo-qr-029', NULL, NULL, '2026-11-02 18:19:00'),
  ('51614f30-816f-5bdc-8f17-5c3db09555d0', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', 'e1192882-1157-5928-8f4e-b907cad0c35e', 'prensa', 'activa', '6a1c9f08-c4cc-5124-ad82-d6f98f3c5901', 'demo-qr-030', NULL, NULL, '2026-11-02 18:30:00'),
  ('14eaf7f5-ab13-5ac9-ab44-baa055ba223f', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '27c894cf-bff3-501a-a842-be2b6b0d7f74', 'general', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 18:41:00'),
  ('96ee9e2f-a14b-52ab-9e33-9d22c632390e', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '653fa7ab-7f55-5b9d-9362-5627dc133163', 'general', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 18:52:00'),
  ('6cf891ae-c2b9-5564-9e39-eec44a0ed30a', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '5704d7e2-0919-5356-a2c7-6f6bcc8eda45', 'negocios', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 19:03:00'),
  ('fa09c839-9666-55ed-8248-401f37345978', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '49d10a81-ff48-573a-ba6d-a66a60c163b4', 'general', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 19:14:00'),
  ('ce08df1f-cab9-57a7-8a2e-acf71ffab59b', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '4b8d9fff-e783-55b7-a98d-f67706ed6000', 'prensa', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 19:25:00'),
  ('3c1566f4-05a1-5d27-b133-be47dca48810', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '6088a3bf-51ad-5f13-b835-c3a4c59f74f3', 'general', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 19:36:00'),
  ('4a25f52e-b156-5152-80ad-9373808a7f61', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', 'a016b6d7-8a58-58a0-96aa-c5d7cb348ffd', 'general', 'pendiente_pago', NULL, NULL, NULL, NULL, '2026-11-02 19:47:00'),
  ('0fbc10fb-5e76-5419-8d07-5899ee331e22', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', 'df886d3c-421b-56eb-a26a-2b5df2cb1e2b', 'negocios', 'cancelada', NULL, NULL, NULL, NULL, '2026-11-02 19:58:00'),
  ('595874c9-47eb-5344-9f93-8f686ae028ab', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '964db46d-079e-53a5-919b-99c3ff407d5c', 'general', 'cancelada', NULL, NULL, NULL, NULL, '2026-11-02 20:09:00'),
  ('013d1748-7fc6-56c4-8ad3-0eabecb36e63', '18fb431a-7d31-5ee7-ae16-402f2199bcd5', '92bf56c0-70d9-5d1d-adb9-533e0dada1c4', 'prensa', 'cancelada', NULL, NULL, NULL, NULL, '2026-11-02 20:20:00')
) AS s (id, evento_id, usuario_id, tipo, estado, orden_pago_id, codigo_qr, usada_en, usada_en_dispositivo, creada_en)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.evento_id = s.evento_id, t.usuario_id = s.usuario_id, t.tipo = s.tipo, t.estado = s.estado, t.orden_pago_id = s.orden_pago_id, t.codigo_qr = s.codigo_qr, t.usada_en = s.usada_en, t.usada_en_dispositivo = s.usada_en_dispositivo, t.creada_en = s.creada_en
WHEN NOT MATCHED THEN INSERT (id, evento_id, usuario_id, tipo, estado, orden_pago_id, codigo_qr, usada_en, usada_en_dispositivo, creada_en) VALUES (s.id, s.evento_id, s.usuario_id, s.tipo, s.estado, s.orden_pago_id, s.codigo_qr, s.usada_en, s.usada_en_dispositivo, s.creada_en);
GO

-- disponibilidad: 10
MERGE dbo.disponibilidad AS t
USING (VALUES
  ('da6ce86f-5a95-5473-8a6f-e9593a54e22b', 'a177e696-49b4-5d09-abde-2d59bd1e7a02', 'd4436d99-db9d-57eb-a07d-f133467a819b', '2026-11-25 14:00:00', '2026-11-25 20:00:00'),
  ('5fcd57af-523a-5263-ab30-c96309600af7', 'd79f291a-472f-50b0-9a29-4459030ba085', 'd4436d99-db9d-57eb-a07d-f133467a819b', '2026-11-25 14:00:00', '2026-11-25 20:00:00'),
  ('e9fe72d2-e6ba-5991-a55f-4711044b19b7', '627b22d8-06a4-578d-a530-6dc2023a9161', 'd4436d99-db9d-57eb-a07d-f133467a819b', '2026-11-25 14:00:00', '2026-11-25 20:00:00'),
  ('1c9f4c44-1e7b-5c83-a043-542f9a90622e', '7c2e3120-fae3-57a6-a41c-b2ec72fe95be', 'd4436d99-db9d-57eb-a07d-f133467a819b', '2026-11-25 14:00:00', '2026-11-25 20:00:00'),
  ('b4595a73-2d0c-5e7f-8f9e-64d9afc267bc', 'ddd244ae-1f98-5dca-9159-1768a3be5469', 'd4436d99-db9d-57eb-a07d-f133467a819b', '2026-11-25 14:00:00', '2026-11-25 20:00:00'),
  ('830937c4-949c-58b8-8c57-37eb4908d1dd', '6563dc18-6925-5bf6-b6b5-c4346f0d0695', 'd4436d99-db9d-57eb-a07d-f133467a819b', '2026-11-25 14:00:00', '2026-11-25 20:00:00'),
  ('c138b329-5c8b-532c-a3e4-2b8e89b0e803', '198cce25-3f14-535f-b08e-eda81fe5214b', 'd4436d99-db9d-57eb-a07d-f133467a819b', '2026-11-25 14:00:00', '2026-11-25 20:00:00'),
  ('18782410-73cb-5680-9b61-914ae30b8257', 'cd34c792-8f86-5f1b-827c-340492b1cbf9', 'd4436d99-db9d-57eb-a07d-f133467a819b', '2026-11-25 14:00:00', '2026-11-25 20:00:00'),
  ('7829ff09-e81b-5948-9686-beabbe216cf3', '832ed401-4b38-5749-a3f6-2ce03953d45d', 'd4436d99-db9d-57eb-a07d-f133467a819b', '2026-11-25 14:00:00', '2026-11-25 20:00:00'),
  ('8d39ec55-1379-5bec-abd4-4a01795a2fa6', 'e0dfa9d1-3e16-5daf-9197-bb4a47f04af0', 'd4436d99-db9d-57eb-a07d-f133467a819b', '2026-11-25 14:00:00', '2026-11-25 20:00:00')
) AS s (id, usuario_id, evento_id, desde, hasta)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.usuario_id = s.usuario_id, t.evento_id = s.evento_id, t.desde = s.desde, t.hasta = s.hasta
WHEN NOT MATCHED THEN INSERT (id, usuario_id, evento_id, desde, hasta) VALUES (s.id, s.usuario_id, s.evento_id, s.desde, s.hasta);
GO

-- citas: 20
MERGE dbo.citas AS t
USING (VALUES
  ('ec5af6be-ea35-5aae-8ba2-534781f0b8e3', 'd4436d99-db9d-57eb-a07d-f133467a819b', '186532f0-d614-5680-8cfe-4177869fba67', 'a177e696-49b4-5d09-abde-2d59bd1e7a02', 'f80e3eca-1ba7-51f5-a57c-562577edac54', '2026-11-25 14:00:00', '2026-11-25 14:30:00', 'aceptada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:01:00'),
  ('f9d361a3-1302-51de-a947-6f550389934d', 'd4436d99-db9d-57eb-a07d-f133467a819b', '67aa2594-cb2e-5801-b731-5cbf8504897e', 'd79f291a-472f-50b0-9a29-4459030ba085', 'a279fadc-96f3-5766-a697-0dd0be5e02a5', '2026-11-25 14:30:00', '2026-11-25 15:00:00', 'aceptada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:02:00'),
  ('e81e1e71-2b4a-5e40-a3a8-25eedf40c93f', 'd4436d99-db9d-57eb-a07d-f133467a819b', '6fa7aed3-f33b-54fe-82b6-2fd72721bea7', '627b22d8-06a4-578d-a530-6dc2023a9161', '710c3d78-9972-5f7e-99b1-71827c91098d', '2026-11-25 15:00:00', '2026-11-25 15:30:00', 'aceptada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:03:00'),
  ('8dbed62f-1bd5-5dbb-aa8b-798fd64b8ce2', 'd4436d99-db9d-57eb-a07d-f133467a819b', '61770e1d-e345-5165-b7e8-92cbbe0ae957', '7c2e3120-fae3-57a6-a41c-b2ec72fe95be', 'ba0d80c2-65f6-5864-9fd4-50fba13aabe2', '2026-11-25 15:30:00', '2026-11-25 16:00:00', 'aceptada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:04:00'),
  ('d276aae1-5b1f-5974-8726-9b4fbb2117e7', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'e1192882-1157-5928-8f4e-b907cad0c35e', 'ddd244ae-1f98-5dca-9159-1768a3be5469', '92ee0c3f-31d3-5fb9-8053-05837dafcc20', '2026-11-25 16:00:00', '2026-11-25 16:30:00', 'aceptada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:05:00'),
  ('65bef9fa-3df3-5eaf-aaf1-7f5ee786f819', 'd4436d99-db9d-57eb-a07d-f133467a819b', '27c894cf-bff3-501a-a842-be2b6b0d7f74', '6563dc18-6925-5bf6-b6b5-c4346f0d0695', 'f1a91078-400b-5bf0-ab30-bea030842de0', '2026-11-25 16:30:00', '2026-11-25 17:00:00', 'aceptada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:06:00'),
  ('b1335f98-8c94-587d-a5be-77dc6ecde090', 'd4436d99-db9d-57eb-a07d-f133467a819b', '653fa7ab-7f55-5b9d-9362-5627dc133163', '198cce25-3f14-535f-b08e-eda81fe5214b', '1ee12ecd-8c42-53b2-af3e-dd185b4f543a', '2026-11-25 17:00:00', '2026-11-25 17:30:00', 'aceptada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:07:00'),
  ('bf7577b8-37a8-5b97-b45d-2750186bff7b', 'd4436d99-db9d-57eb-a07d-f133467a819b', '5704d7e2-0919-5356-a2c7-6f6bcc8eda45', 'cd34c792-8f86-5f1b-827c-340492b1cbf9', '7a1a57f8-9351-513b-a9ed-b9714cfccd4f', '2026-11-25 17:30:00', '2026-11-25 18:00:00', 'aceptada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:08:00'),
  ('3dc32826-69df-5e77-93d5-0b3be6d9ba9b', 'd4436d99-db9d-57eb-a07d-f133467a819b', '49d10a81-ff48-573a-ba6d-a66a60c163b4', '832ed401-4b38-5749-a3f6-2ce03953d45d', NULL, '2026-11-25 18:00:00', '2026-11-25 18:30:00', 'propuesta', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:09:00'),
  ('f9e57a6a-c4ef-510b-9a3c-c62dc3547bae', 'd4436d99-db9d-57eb-a07d-f133467a819b', '4b8d9fff-e783-55b7-a98d-f67706ed6000', 'e0dfa9d1-3e16-5daf-9197-bb4a47f04af0', NULL, '2026-11-25 18:30:00', '2026-11-25 19:00:00', 'propuesta', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:10:00'),
  ('2c321f3f-234e-5b2b-8c96-b83b77c0b6b4', 'd4436d99-db9d-57eb-a07d-f133467a819b', '6088a3bf-51ad-5f13-b835-c3a4c59f74f3', 'a177e696-49b4-5d09-abde-2d59bd1e7a02', NULL, '2026-11-25 19:00:00', '2026-11-25 19:30:00', 'propuesta', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:11:00'),
  ('ab5e042c-3810-5237-840d-5704c0c2e2d4', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'a016b6d7-8a58-58a0-96aa-c5d7cb348ffd', 'd79f291a-472f-50b0-9a29-4459030ba085', NULL, '2026-11-25 19:30:00', '2026-11-25 20:00:00', 'propuesta', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:12:00'),
  ('0a5b9911-c83c-509e-9182-b66c2e1c06f8', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'df886d3c-421b-56eb-a26a-2b5df2cb1e2b', '627b22d8-06a4-578d-a530-6dc2023a9161', NULL, '2026-11-25 20:00:00', '2026-11-25 20:30:00', 'propuesta', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:13:00'),
  ('5fa9f6e0-1f2d-58a2-8eb8-e399b6eb6f70', 'd4436d99-db9d-57eb-a07d-f133467a819b', '964db46d-079e-53a5-919b-99c3ff407d5c', '7c2e3120-fae3-57a6-a41c-b2ec72fe95be', NULL, '2026-11-25 20:30:00', '2026-11-25 21:00:00', 'propuesta', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:14:00'),
  ('c8ddccff-4647-53bb-aed1-53b341496f18', 'd4436d99-db9d-57eb-a07d-f133467a819b', '92bf56c0-70d9-5d1d-adb9-533e0dada1c4', 'ddd244ae-1f98-5dca-9159-1768a3be5469', NULL, '2026-11-25 21:00:00', '2026-11-25 21:30:00', 'rechazada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:15:00'),
  ('e2994267-89e4-5420-972a-08f07872620c', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'd70cade7-766f-50ee-935a-1e8a35deda24', '6563dc18-6925-5bf6-b6b5-c4346f0d0695', NULL, '2026-11-25 21:30:00', '2026-11-25 22:00:00', 'rechazada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:16:00'),
  ('10d7fc79-ba17-5818-b96b-db023dee8917', 'd4436d99-db9d-57eb-a07d-f133467a819b', 'e42cb46f-a779-5157-87f1-a57f56acc71d', '198cce25-3f14-535f-b08e-eda81fe5214b', NULL, '2026-11-25 22:00:00', '2026-11-25 22:30:00', 'rechazada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:17:00'),
  ('5e25418c-1e69-5405-9d13-39f6853a0191', 'd4436d99-db9d-57eb-a07d-f133467a819b', '4689cd87-ed8a-5d8c-8d6c-7a657a628efb', 'cd34c792-8f86-5f1b-827c-340492b1cbf9', NULL, '2026-11-25 22:30:00', '2026-11-25 23:00:00', 'rechazada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:18:00'),
  ('85fc11fb-9f51-5623-85ff-688c17c26fb2', 'd4436d99-db9d-57eb-a07d-f133467a819b', '10aa85bd-4011-5187-8f1f-334ed61ed85d', '832ed401-4b38-5749-a3f6-2ce03953d45d', NULL, '2026-11-25 23:00:00', '2026-11-25 23:30:00', 'cancelada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:19:00'),
  ('99fc219c-b293-5a0e-a228-2435d643a4ba', 'd4436d99-db9d-57eb-a07d-f133467a819b', '415bc3de-3e44-5c96-bc64-f3381402cbfb', 'e0dfa9d1-3e16-5daf-9197-bb4a47f04af0', NULL, '2026-11-25 23:30:00', '2026-11-26 00:00:00', 'cancelada', 'Me interesa conocer su portafolio y condiciones comerciales.', '2026-11-03 13:20:00')
) AS s (id, evento_id, solicitante_id, anfitrion_id, sala_id, inicio, fin, estado, mensaje, creada_en)
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.evento_id = s.evento_id, t.solicitante_id = s.solicitante_id, t.anfitrion_id = s.anfitrion_id, t.sala_id = s.sala_id, t.inicio = s.inicio, t.fin = s.fin, t.estado = s.estado, t.mensaje = s.mensaje, t.creada_en = s.creada_en
WHEN NOT MATCHED THEN INSERT (id, evento_id, solicitante_id, anfitrion_id, sala_id, inicio, fin, estado, mensaje, creada_en) VALUES (s.id, s.evento_id, s.solicitante_id, s.anfitrion_id, s.sala_id, s.inicio, s.fin, s.estado, s.mensaje, s.creada_en);
GO
