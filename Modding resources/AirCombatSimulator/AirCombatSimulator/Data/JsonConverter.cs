using Newtonsoft.Json;

namespace AirCombatSimulator.Data
{
    internal static class JsonConverter
    {
        internal static string Serialize<T>(T data)
        {
            return JsonConvert.SerializeObject(data);
        }

        internal static T Deserialize<T>(string data)
        {
            return JsonConvert.DeserializeObject<T>(data) ?? throw new InvalidOperationException($"Could not deserialize data: {data}");
        }
    }
}
