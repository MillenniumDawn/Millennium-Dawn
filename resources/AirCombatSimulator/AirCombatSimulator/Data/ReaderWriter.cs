namespace AirCombatSimulator.Data
{
    internal static class ReaderWriter
    {
        internal static void Write(string filePath, string data)
        {
            File.WriteAllText(filePath, data);
        }

        internal static string Read(string filePath)
        {
            return File.ReadAllText(filePath);
        }

        internal static bool Exists(string filePath)
        {
            return File.Exists(filePath);
        }
    }
}
