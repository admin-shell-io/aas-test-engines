using System.Text.Json.Nodes;

using Aas = AasCore.Aas3_0;
using AasJsonization = AasCore.Aas3_0.Jsonization;
using AasVerification = AasCore.Aas3_0.Verification;

public class Program
{
    static String[] blacklist = new String[] {
        "Message broker must be a model reference to a referable.",
        "Max. interval is not applicable for input direction.",
        "Observed must be a model reference to a referable.",
        "Derived-from must be a model reference to an asset administration shell.",
        "All submodels must be model references to a submodel.",
        "Constraint AASc-3a-009: If data type is a an integer, real or rational with a measure or currency, unit or unit ID shall be defined.",
    };

    public static String? Check(string file, string out_file)
    {
        string text = File.ReadAllText(file);
        var options = new System.Text.Json.JsonDocumentOptions();
        options.MaxDepth = 1000;
        var jsonNode = JsonNode.Parse(text, null, options);

        if(jsonNode == null)
        {
            return null;
        }

        Aas.Environment environment;
        try
        {
            environment = AasJsonization.Deserialize.EnvironmentFrom(jsonNode);
        }
        catch(AasCore.Aas3_0.Jsonization.Exception e)
        {
            return null;
        }

        foreach (var error in AasVerification.Verify(environment))
        {
            if(!blacklist.Any(error.Cause.Contains))
            {
                return null;
            }
        }

        // deserialize
        var jsonString = AasJsonization.Serialize.ToJsonObject(environment).ToString();
        File.WriteAllText(out_file, jsonString);
        return jsonString;
    }

    public static void Main()
    {
        string[] files = Directory.GetFiles("/test_data");
        foreach(string file in files)
        {
            var result = Check(file, $"/out/{Path.GetFileName(file)}");
        }
    }
}
