using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text.Json;
using Microsoft.TeamFoundation.Client;
using Microsoft.TeamFoundation.Framework.Client;
using Microsoft.TeamFoundation.Framework.Common;
using Microsoft.VisualStudio.Services.Common;

namespace Getuserlist
{
    class Program
    {
        static void Main(string[] args)
        {

            WebRequest.DefaultWebProxy = null;

            if (args.Length < 3)
            {
                Console.WriteLine("Usage: Getuserlist <TFS Uri> <username> <PAT>");
                return;
            }

            string uriArg = args[0];
            if (!Uri.TryCreate(uriArg, UriKind.Absolute, out Uri tfsUri))
            {
                Console.WriteLine("Invalid Uri provided.");
                return;
            }

            string username = args[1];
            string pat = args[2];

            var vssCred = new Microsoft.VisualStudio.Services.Common.VssBasicCredential(username, pat);

            using (TfsTeamProjectCollection tpc = new TfsTeamProjectCollection(tfsUri, vssCred))
            {
                tpc.EnsureAuthenticated();

                IIdentityManagementService ims = tpc.GetService<IIdentityManagementService>();
                TeamFoundationIdentity tfi = ims.ReadIdentity(
                    IdentitySearchFactor.AccountName,
                    "[DefaultCollection]\\Project Collection Valid Users",
                    MembershipQuery.Expanded,
                    ReadIdentityOptions.None
                );
                TeamFoundationIdentity[] ids = ims.ReadIdentities(
                    tfi.Members,
                    MembershipQuery.None,
                    ReadIdentityOptions.None
                );

                int totalUsers = 0;
                var userList = new List<object>();

                foreach (TeamFoundationIdentity id in ids)
                {
                    if (id.Descriptor.IdentityType == "System.Security.Principal.WindowsIdentity" && id.IsContainer == false)
                    {
                        var userObj = new
                        {
                            email = id.GetAttribute("Mail", null),
                            id = id.TeamFoundationId,
                            name = id.DisplayName,
                            state = id.IsActive ? "active" : "inactive",
                            username = id.UniqueName
                        };

                        userList.Add(userObj);
                        totalUsers++;
                    }
                }

                string jsonArray = JsonSerializer.Serialize(userList, new JsonSerializerOptions { WriteIndented = false });
                Console.WriteLine(jsonArray);

                File.WriteAllText("users.json", jsonArray);

                Console.WriteLine($"Total users found: {totalUsers}");
                Console.WriteLine("Press any key to exit...");
                Console.ReadLine();
            }
        }
    }
}