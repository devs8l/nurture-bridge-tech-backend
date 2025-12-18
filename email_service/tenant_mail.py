tenant_mail_template = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  <style type="text/css">
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    @media only screen and (max-width: 768px) {{
      .mobile-padding {{ padding: 15px !important; }}
      .mobile-text-center {{ text-align: start !important; }}
      .mobile-block {{ display: block !important; width: 100% !important; margin-bottom: 10px !important; }}
      .mobile-font-small {{ font-size: 13px !important; }}
      .mobile-font-medium {{ font-size: 15px !important; }}
      .mobile-font-large {{ font-size: 20px !important; }}
      .mobile-logo {{ width: 80px !important; position: static !important; display: block !important; margin: 0 auto 20px auto !important; }}
      .mobile-header {{ text-align: center !important; position: static !important; }}
      .mobile-stack {{ display: block !important; width: 100% !important; margin-bottom: 12px !important; }}
      .mobile-center-content {{ width: 100% !important; }}
    }}
    @media only screen and (max-width: 480px) {{
      .mobile-padding-small {{ padding: 10px !important; }}
      .mobile-font-xs {{ font-size: 12px !important; }}
      .mobile-font-s {{ font-size: 13px !important; }}
      .mobile-font-m {{ font-size: 18px !important; }}
      .mobile-logo-small {{ width: 60px !important; margin: 0 auto 15px auto !important; position: static !important; display: block !important; }}
    }}
  </style>
</head>
<body style="margin: 0; padding: 0; font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333333; width: 100%; min-height: 100vh;">
  
  <!-- Main Container -->
  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 0; padding: 0;">
    <tr>
      <td style="padding: 20px;" class="mobile-padding">
        
        <!-- Email Container -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 1200px; margin: 0 auto;">
          <tr>
            <td>
              
              <!-- Main Content Container -->
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="border: 1px solid #22283633; border-radius: 12px; padding: 10px; margin-bottom: 20px;" class="mobile-padding">
                <tr>
                  <td>
                    
                    <!-- Header Card -->
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: linear-gradient(90deg, #E8F5EE 0%, #FFF 100%); padding: 80px 30px; border-radius: 12px; margin-bottom: 10px; border: 1px solid #22283633; position: relative;" class="mobile-padding mobile-header">
                      <tr>
                        <td style="text-align: center;">
                          <!-- Header Content -->
                          <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center"
                            style="margin: 0 auto;">
                            <tr>
                              <td align="center" valign="middle">
                                <h1
                                  style="color: #1f2937; font-size: 26px; font-weight: 600; margin: 0; line-height: 1.3; font-family: 'Inter', Arial, sans-serif;">
                                  Welcome to Nurture Bridge Tech
                                </h1>
                              </td>
                            </tr>
                          </table>
                          <p style="color: #6b7280; font-size: 14px; margin: 8px 0 0 0; font-weight: 400; text-align: center; font-family: 'Inter', Arial, sans-serif;" class="mobile-font-small">We're excited to have you join the Nurture Bridge Tech community.<br>Your account has been successfully created and is ready to use.</p>
                        </td>
                      </tr>
                    </table>
                    
                    <!-- Cards Container -->
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                      <!-- Login Credentials Card with Security Recommendation -->
                      <tr>
                        <td style="padding-bottom: 10px;">
                          <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="border: 1px solid #22283633; padding: 24px; border-radius: 12px;" class="mobile-padding">
                            <tr>
                              <td style="text-align: center;">
                                <!-- Centered Content Container -->
                                <div style="width: 35%; margin: 0 auto;" class="mobile-center-content">
                                  <h3 style="color: #1f2937; margin: 0 0 30px 0; font-size: 16px; font-weight: 600; text-align: center; font-family: 'Inter', Arial, sans-serif;" class="mobile-font-medium">Your Login Credentials</h3>
                                  
                                  <!-- Credentials Row -->
                                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 20px;">
                                    <tr>
                                      <!-- Username Field -->
                                      <td style="width: 50%; padding-right: 5px;" class="mobile-stack">
                                        <div style="border: 1px solid #22283633; padding: 8px; background-color: #22283605; border-radius: 8px; text-align: center;">
                                          <span style="color: #1f2937; font-size: 14px; display: block; margin-bottom: 4px; font-family: 'Inter', Arial, sans-serif;" class="mobile-font-s">Username/Email:</span>
                                          <span style="color:#6b7280; font-size:14px; font-weight:500; text-decoration:none !important; font-family:'Inter', Arial, sans-serif; display:inline-block;">{identifier}</span>
                                        </div>
                                      </td>
                                      
                                      <!-- Password Field -->
                                      <td style="width: 50%; padding-left: 5px;" class="mobile-stack">
                                        <div style="border: 1px solid #22283633; padding: 8px; background-color: #22283605; border-radius: 8px; text-align: center;">
                                          <span style="color: #1f2937; font-size: 14px; display: block; margin-bottom: 4px; font-family: 'Inter', Arial, sans-serif;" class="mobile-font-s">Password:</span>
                                          <span style="color: #6b7280; font-size: 14px; font-weight: 500; font-family: 'Inter', Arial, sans-serif;" class="mobile-font-s">{password}</span>
                                        </div>
                                      </td>
                                    </tr>
                                  </table>
                                  
                                  <!-- CTA Button -->
                                  <div style="text-align: center; margin-bottom: 20px;">
                                    <a href="https://nbt-admin.vercel.app/{tenant_id}" style="background-color: #53AC73; color: white; padding: 16px 0; text-decoration: none; border-radius: 8px;background: #53AC73;box-shadow: 0 4px 10px 0 rgba(34, 40, 54, 0.05); font-weight: 500; display: block; width: 100%; font-size: 14px; font-family: 'Inter', Arial, sans-serif; box-sizing: border-box;" class="mobile-font-s">
                                      Click here to login
                                    </a>
                                  </div>
                                  
                                  <!-- Security Recommendation Section -->
                                  <div style=" padding: 20px 0px;">
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                      <tr>
                                        <td style="width: 40px; vertical-align: top; padding-right: 12px; text-align: center;">
                                          <!-- Security Icon -->
                                          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: block; margin: 0 auto;">
                                            <path d="M12 2L4 6V12C4 16.55 7.16 20.74 12 22C16.84 20.74 20 16.55 20 12V6L12 2ZM12 12H18C17.78 15.37 15.62 18.27 12 19.66V12H6V7.3L12 4.19V12Z" fill="#53AC73"/>
                                          </svg>
                                        </td>
                                        <td style="vertical-align: top; text-align: left;">
                                          <p style="color: #6b7280; font-size: 12px; margin: 0; line-height: 1.5; font-family: 'Inter', Arial, sans-serif;" class="mobile-font-s">For your account's security, we strongly recommend that you change your password after your first login.</p>
                                        </td>
                                      </tr>
                                    </table>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                      
                      <!-- Reach Out to Us Card -->
                      <tr>
                        <td>
                          <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="border: 1px solid #22283633; padding: 24px; border-radius: 12px; background-color: #f8f9fa;" class="mobile-padding">
                            <tr>
                              <td style="text-align: center;">
                                <!-- Centered Content Container -->
                                <div style="width: 35%; margin: 0 auto;" class="mobile-center-content">
                                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                    <tr>
                                      <td style="width: 40px; vertical-align: top; padding-right: 12px; text-align: center;">
                                        <!-- Heart Icon -->
                                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: block; margin: 0 auto;">
                                          <path d="M12 21.35L10.55 20.03C5.4 15.36 2 12.27 2 8.5C2 5.41 4.42 3 7.5 3C9.24 3 10.91 3.81 12 5.08C13.09 3.81 14.76 3 16.5 3C19.58 3 22 5.41 22 8.5C22 12.27 18.6 15.36 13.45 20.03L12 21.35Z" fill="#53AC73"/>
                                        </svg>
                                      </td>
                                      <td style="vertical-align: top; text-align: left;">
                                        <p style="color: #6b7280; font-size: 12px; margin: 0; line-height: 1.5; font-family: 'Inter', Arial, sans-serif;" class="mobile-font-s">If you encounter any issues during login or have any questions, please contact our support team. Welcome aboard and we're here to help you grow!</p>
                                      </td>
                                    </tr>
                                  </table>
                                </div>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                    
                  </td>
                </tr>
              </table>
              
            </td>
          </tr>
        </table>
        
        <!-- Footer -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 1200px; margin: 0 auto;">
          <tr>
            <td style="text-align: center; padding: 20px;">
              <p style="font-size: 11px; color: #9ca3af; margin: 0; font-family: 'Inter', Arial, sans-serif;" class="mobile-font-xs">
                This is an automated message. Please do not reply to this email.
              </p>
            </td>
          </tr>
        </table>
        
      </td>
    </tr>
  </table>
  
</body>
</html>
"""