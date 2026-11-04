using System.Text;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
using MongoDB.Bson.Serialization.Conventions;
using MongoDB.Bson.Serialization.Serializers;

namespace MesaAyuda.Api.Datos;

/// <summary>
/// Formato de los documentos en MongoDB: campos en snake_case, igual que el JSON de la API
/// (ADR-014), y fechas como fechas BSON en UTC. Así la colección de series de tiempo de lecturas
/// encuentra su campo de tiempo (`momento`) y los datos se pueden consultar e insertar a mano.
/// </summary>
public static class MongoConventions
{
    private static int _registered;

    public static void Register()
    {
        if (Interlocked.Exchange(ref _registered, 1) == 1)
        {
            return;
        }

        ConventionRegistry.Register(
            "exponexo-snake-case",
            new ConventionPack { new SnakeCaseElementNameConvention() },
            type => type.Namespace?.StartsWith("MesaAyuda.Api", StringComparison.Ordinal) == true);
        BsonSerializer.TryRegisterSerializer(new DateTimeOffsetSerializer(BsonType.DateTime));
    }

    private sealed class SnakeCaseElementNameConvention : ConventionBase, IMemberMapConvention
    {
        public void Apply(BsonMemberMap memberMap)
        {
            // El identificador conserva "_id" (lo fija [BsonId])
            if (memberMap.MemberName != "Id")
            {
                memberMap.SetElementName(ToSnakeCase(memberMap.MemberName));
            }
        }

        private static string ToSnakeCase(string name)
        {
            var builder = new StringBuilder(name.Length + 8);
            for (var i = 0; i < name.Length; i++)
            {
                if (char.IsUpper(name[i]) && i > 0)
                {
                    builder.Append('_');
                }
                builder.Append(char.ToLowerInvariant(name[i]));
            }
            return builder.ToString();
        }
    }
}
