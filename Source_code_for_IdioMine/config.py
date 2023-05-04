import javalang 

# The default settings
CFGType = (javalang.tree.IfStatement, javalang.tree.WhileStatement, javalang.tree.DoStatement, javalang.tree.ForStatement,
            javalang.tree.TryStatement, javalang.tree.SwitchStatement, javalang.tree.BreakStatement, javalang.tree.ContinueStatement, javalang.tree.SynchronizedStatement)

# AST_to_Code_Type = (javalang.tree.IfStatement, javalang.tree.WhileStatement, javalang.tree.DoStatement, javalang.tree.ForStatement,
#             javalang.tree.TryStatement, javalang.tree.SwitchStatement, javalang.tree.BreakStatement, javalang.tree.ContinueStatement, javalang.tree.SynchronizedStatement)

treeNodeType = (javalang.tree.CompilationUnit, javalang.tree.Import, javalang.tree.Documented, javalang.tree.Declaration, 
                javalang.tree.TypeDeclaration, javalang.tree.PackageDeclaration, javalang.tree.ClassDeclaration, 
                javalang.tree.EnumDeclaration, javalang.tree.InterfaceDeclaration, javalang.tree.AnnotationDeclaration,
                javalang.tree.Type, javalang.tree.BasicType, javalang.tree.ReferenceType, javalang.tree.TypeArgument,
                javalang.tree.TypeParameter, javalang.tree.Annotation, javalang.tree.ElementValuePair, javalang.tree.ElementArrayValue,
                javalang.tree.Member, javalang.tree.MethodDeclaration, javalang.tree.FieldDeclaration, javalang.tree.ConstructorDeclaration,
                javalang.tree.ConstantDeclaration, javalang.tree.ArrayInitializer, javalang.tree.VariableDeclaration,
                javalang.tree.LocalVariableDeclaration, javalang.tree.VariableDeclarator, javalang.tree.FormalParameter,
                javalang.tree.InferredFormalParameter, javalang.tree.Statement, javalang.tree.IfStatement, javalang.tree.WhileStatement,
                javalang.tree.DoStatement, javalang.tree.ForStatement, javalang.tree.AssertStatement, javalang.tree.BreakStatement,
                javalang.tree.ContinueStatement, javalang.tree.ReturnStatement, javalang.tree.ThrowStatement, javalang.tree.SynchronizedStatement, 
                javalang.tree.TryStatement, javalang.tree.SwitchStatement, javalang.tree.BlockStatement, javalang.tree.StatementExpression, 
                javalang.tree.TryResource, javalang.tree.CatchClause, javalang.tree.CatchClauseParameter, javalang.tree.SwitchStatementCase, 
                javalang.tree.ForControl, javalang.tree.EnhancedForControl, javalang.tree.Expression, javalang.tree.Assignment,
                javalang.tree.TernaryExpression, javalang.tree.BinaryOperation, javalang.tree.Cast, javalang.tree.MethodReference, 
                javalang.tree.LambdaExpression, javalang.tree.Primary, javalang.tree.Literal, javalang.tree.This, javalang.tree.MemberReference,
                javalang.tree.Invocation, javalang.tree.ExplicitConstructorInvocation, javalang.tree.SuperConstructorInvocation,
                javalang.tree.MethodInvocation, javalang.tree.SuperMethodInvocation, javalang.tree.SuperMemberReference,
                javalang.tree.ArraySelector, javalang.tree.ClassReference, javalang.tree.VoidClassReference, javalang.tree.Creator,
                javalang.tree.ArrayCreator, javalang.tree.ClassCreator, javalang.tree.InnerClassCreator, javalang.tree.EnumBody,
                javalang.tree.EnumConstantDeclaration, javalang.tree.AnnotationMethod
                )

DFGDefType_declators = (javalang.tree.VariableDeclaration, javalang.tree.LocalVariableDeclaration, javalang.tree.FieldDeclaration, javalang.tree.ConstantDeclaration)

DFGDefType_name = (javalang.tree.TypeDeclaration, javalang.tree.EnumDeclaration, javalang.tree.EnumConstantDeclaration,
                javalang.tree.PackageDeclaration, javalang.tree.ClassDeclaration, javalang.tree.InterfaceDeclaration, javalang.tree.MethodDeclaration,
                javalang.tree.ConstructorDeclaration)

DFGDefType_name_value = (javalang.tree.TryResource)

DFGUseType_member_prefix_operators = (javalang.tree.MethodInvocation, javalang.tree.SuperMethodInvocation)

DFGUseType_expression = (javalang.tree.ReturnStatement, javalang.tree.ThrowStatement, javalang.tree.SwitchStatement, javalang.tree.StatementExpression)

DFGUseType_arguments = (javalang.tree.ClassCreator,javalang.tree.InnerClassCreator)

DFGUseType_others = (javalang.tree.Assignment, javalang.tree.BinaryOperation, javalang.tree.Cast, javalang.tree.MethodReference, 
                    javalang.tree.LambdaExpression, javalang.tree.TernaryExpression) # expression


DFGType_name = (javalang.tree.VariableDeclarator, javalang.tree.CatchClauseParameter,
            javalang.tree.TypeParameter) #  javalang.tree.FormalParameter, javalang.tree.InferredFormalParameter, 

DFGType_member = (javalang.tree.MemberReference, javalang.tree.SuperMemberReference)